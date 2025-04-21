# dhl_rerouter_poc/main.py

import argparse
from .logging_utils import debug_log_model
import logging
from .email_client        import ImapEmailClient
from .parser              import extract_tracking_codes
from .calendar_checker    import should_reroute
from dhl_rerouter_poc.carriers.base import CarrierBase
from dhl_rerouter_poc.carriers.dhl import DHLCarrier
import logging
from .config              import load_config
from .workflow_data_model import (
    ShipmentLifecycle,
    TransportProviderInfo,
    ConsignmentNotification,
    ShipmentTrackingInfo,
    RecipientAvailability,
    DeliveryInterventionResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dhl_rerouter")

def reroute_shipment(
    tracking_number: str,
    zip_code: str,
    custom_location: str,
    highlight_only: bool = True,
    selenium_headless: bool = False,
    timeout: int = 20
) -> bool:
    """
    Backward-compatible wrapper for reroute_shipment, for test mocking and legacy code.
    Currently delegates to DHLCarrier. Update to support other carriers if needed.
    """
    handler = DHLCarrier()
    return handler.reroute_shipment(
        tracking_number,
        zip_code,
        custom_location,
        highlight_only,
        selenium_headless,
        timeout
    )

def run(
    weeks: int | None = None,
    zip_code: str | None = None,
    custom_location: str | None = None,
    highlight_only: bool = True,
    selenium_headless: bool = False,
    timeout: int = 20,
    config: dict | None = None
) -> None:
    client = ImapEmailClient(config["email"])
    if weeks:
        client.lookback = weeks
    bodies = client.fetch_messages()

    seen: set[str] = set()
    carrier_registry: dict[str, type[CarrierBase]] = {
        "DHL": DHLCarrier,
        # Add future carriers here
    }
    logger = logging.getLogger(__name__)
    carrier_configs: dict = config.get("carrier_configs", {})
    for body in bodies:
        codes = extract_tracking_codes(body, config["tracking_patterns"])
        for code, carrier in sorted(codes.items()):
            if code in seen:
                continue
            seen.add(code)
            logger.info(f"Processing tracking code: %s (carrier: %s)", code, carrier)

            # --- Build ShipmentLifecycle context ---
            shipment = ShipmentLifecycle(
                provider=TransportProviderInfo(name=carrier, tracking_number=code),
                notification=ConsignmentNotification(
                    normalized_body=body[:4096],
                    body_truncated=len(body) > 4096,
                    # Optionally fill subject/sender/received_at if available from client
                ),
            )
            debug_log_model(shipment, "after init")

            # skip unsupported carriers (model-driven + registry)
            carrier_cls = carrier_registry.get(carrier)
            if not shipment.provider.is_supported() or not carrier_cls:
                logger.info("  → skipping unsupported carrier: %s", carrier)
                continue
            carrier_handler: CarrierBase = carrier_cls()

            # --- Carrier config merge ---
            carrier_cfg = carrier_configs.get(carrier, {})
            carrier_zip = zip_code or carrier_cfg.get("zip")
            carrier_location = custom_location or carrier_cfg.get("reroute_location")
            carrier_highlight = highlight_only if highlight_only is not None else carrier_cfg.get("highlight_only", True)
            carrier_headless = selenium_headless if selenium_headless is not None else carrier_cfg.get("selenium_headless", True)
            carrier_timeout = timeout if timeout is not None else carrier_cfg.get("timeout", 20)

            # --- Tracking info (via handler) ---
            info = carrier_handler.check_reroute_availability(code, carrier_zip, timeout=carrier_timeout)
            shipment.tracking = ShipmentTrackingInfo(
                status=info.get("delivery_status", "unknown"),
                delivered=info.get("delivered", False),
                delivery_date=info.get("delivery_date"),
                delivery_status=info.get("delivery_status"),
                delivery_options=info.get("delivery_options", []),
                shipment_history=info.get("shipment_history", []),
                custom_dropoff_input_present=info.get("custom_dropoff_input_present", False),
                protocol=info.get("protocol", {}),
                last_checked=None,
                status_code=None,
            )
            debug_log_model(shipment, "after tracking")
            date_iso = shipment.tracking.delivery_date
            opts     = shipment.tracking.delivery_options
            errors   = shipment.tracking.protocol.get("errors", [])

            if errors:
                logger.warning(f"  ⚠️ encountered errors: {errors}")

            # --- Calendar-based decision ---
            if not date_iso:
                logger.info("  → no delivery_date parsed; skipping calendar check")
                continue
            logger.info(f"  → checking calendar for delivery_date={date_iso}")
            should = should_reroute(code, date_iso, config)
            shipment.recipient_availability = RecipientAvailability(
                delivery_date=date_iso,
                is_away=not should,
                overlapping_absences=[],  # Could be filled by should_reroute in future
                sources_checked=[],
            )
            debug_log_model(shipment, "after calendar check")
            logger.info(f"  → should_reroute returned {should}")
            if not should:
                logger.info(f"  → skipped by calendar (delivery_date={date_iso})")
                continue

            # --- Availability check ---
            if not opts:
                logger.info("  → no reroute options available")
                continue
            logger.info(f"  → available options: {opts}")

            # --- Execute reroute (via handler) ---
            logger.info(f"  → performing reroute (highlight_only={carrier_highlight})")
            # Use main.reroute_shipment wrapper to allow test patching
            from dhl_rerouter_poc import main as main_mod
            success = main_mod.reroute_shipment(
                code, carrier_zip, carrier_location,
                carrier_highlight,
                selenium_headless,
                timeout
            )
            shipment.intervention = DeliveryInterventionResult(
                attempted=True,
                success=success,
                error=None if success else "reroute failed",
                timestamp=None,
                attempts=1,
                status_code=200 if success else 500,
                detail=None,
            )
            debug_log_model(shipment, "after intervention")
            logger.info(f"  → reroute {'✅' if success else '❌'}")

def main():
    config = load_config()
    weeks_default = config.get("email", {}).get("lookback_weeks")
    carrier_configs = config.get("carrier_configs", {})
    dhl_cfg = carrier_configs.get("DHL", {})
    zip_default = dhl_cfg.get("zip")
    location_default = dhl_cfg.get("reroute_location")
    highlight_default = dhl_cfg.get("highlight_only", True)
    selenium_headless_default = dhl_cfg.get("selenium_headless", True)
    timeout_default = dhl_cfg.get("timeout", 20)

    p = argparse.ArgumentParser()
    p.add_argument(
        "--weeks", type=int,
        help=f"Override lookback period (weeks back to search emails; overrides config if set) [default: {weeks_default}]"
    )
    p.add_argument(
        "--zip", dest="zip_code", required=False,
        help=f"Postal code for DHL tracking page (overrides config if set) [default: {zip_default}]"
    )
    p.add_argument(
        "--location", dest="custom_location", required=False,
        help=f"Custom drop‑off location text (overrides config if set) [default: {location_default}]"
    )
    p.set_defaults(
        weeks=weeks_default,
        zip_code=zip_default,
        custom_location=location_default,
        highlight_only=highlight_default,
        selenium_headless=selenium_headless_default,
        timeout=timeout_default
    )
    p.add_argument(
        "--highlight-only", action="store_true", help=f"Highlight only, do not click confirm (overrides config) [default: {highlight_default}]"
    )
    p.add_argument(
        "--selenium-headless", action="store_true", help=f"Run Selenium in headless mode (overrides config) [default: {selenium_headless_default}]"
    )
    p.add_argument(
        "--timeout", type=int, help=f"Timeout for Selenium waits (overrides config) [default: {timeout_default}]"
    )
    args = p.parse_args()
    # CLI always takes precedence if explicitly set
    highlight_only = args.highlight_only if 'highlight_only' in args else highlight_default
    selenium_headless = args.selenium_headless if 'selenium_headless' in args else selenium_headless_default
    timeout = args.timeout if args.timeout is not None else timeout_default
    # Validate required parameters
    if not args.zip_code:
        raise ValueError("A zip code must be provided via --zip or config.yaml under carriers:DHL:zip")
    if not args.custom_location:
        raise ValueError("A reroute location must be provided via --location or config.yaml under carriers:DHL:reroute_location")
    if args.weeks is None:
        raise ValueError("A lookback period must be provided via --weeks or config.yaml under email:lookback_weeks")
    run(args.weeks, args.zip_code, args.custom_location, highlight_only, selenium_headless, timeout)

if __name__ == "__main__":
    main()
