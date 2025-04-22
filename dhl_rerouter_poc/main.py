# dhl_rerouter_poc/main.py

import argparse
import logging
from .calendar_checker import should_reroute
from .config import load_config
from .email_client_imap import ImapEmailClient
from .email_client_msgraph import EmailClientMsGraph
from .logging_utils import debug_log_model
from .parser import extract_tracking_codes
from dhl_rerouter_poc.carriers.base import CarrierBase
from dhl_rerouter_poc.carriers.dhl import DHLCarrier
from .workflow_data_model import (
    ConsignmentNotification,
    DeliveryInterventionResult,
    RecipientAvailability,
    ShipmentLifecycle,
    ShipmentTrackingInfo,
    TransportProviderInfo,
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
    timeout: int = 20,
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
        timeout,
    )


def run(
    lookback_weeks: int | None = None,
    zip_code: str | None = None,
    custom_location: str | None = None,
    highlight_only: bool = True,
    selenium_headless: bool = False,
    timeout: int = 20,
    config: dict | None = None,
) -> None:
    """
    Main execution function.
    """
    logger = logging.getLogger(__name__)
    mailboxes = config.get("mailboxes", [])
    all_bodies = []

    for mailbox in mailboxes:
        mtype = mailbox.get("type")
        if not mtype:
            logger.warning(f"Mailbox '{mailbox.get('name','?')}' missing 'type', skipping.")
            continue
        mtype = mtype.lower()
        if mtype == "imap":
            client = ImapEmailClient(mailbox)
        elif mtype == "msgraph":
            client = EmailClientMsGraph(mailbox)
        else:
            logger.warning(f"Unknown mailbox type '{mtype}' for mailbox '{mailbox.get('name','?')}', skipping.")
            continue
        if lookback_weeks:
            client.lookback = lookback_weeks
        bodies = client.fetch_messages()
        all_bodies.extend(bodies)

    seen: set[str] = set()
    carrier_registry: dict[str, type[CarrierBase]] = {
        "DHL": DHLCarrier,
        # Add future carriers here
    }
    logger = logging.getLogger(__name__)
    carrier_configs: dict = config.get("carrier_configs", {})
    for body in all_bodies:
        codes = extract_tracking_codes(body, config["tracking_patterns"])
        for code, carrier in sorted(codes.items()):
            if code in seen:
                continue
            seen.add(code)
            logger.info(f"Going to process tracking code: %s (carrier: %s)", code, carrier)

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
            carrier_highlight = (
                highlight_only if highlight_only is not None else carrier_cfg.get("highlight_only", True)
            )
            carrier_headless = (
                selenium_headless if selenium_headless is not None else carrier_cfg.get("selenium_headless", True)
            )
            carrier_timeout = timeout if timeout is not None else carrier_cfg.get("timeout", 20)

            # --- Tracking info (via handler) ---
            info = carrier_handler.check_reroute_availability(
                code,
                carrier_zip,
                timeout=carrier_timeout,
                selenium_headless=carrier_headless,
            )
            shipment.tracking = ShipmentTrackingInfo(
                status=info.data.get("delivery_status", "unknown"),
                delivered=info.data.get("delivered", False),
                delivery_date=info.data.get("delivery_date"),
                delivery_status=info.data.get("delivery_status"),
                delivery_options=info.data.get("delivery_options", []),
                shipment_history=info.data.get("shipment_history", []),
                custom_dropoff_input_present=info.data.get("custom_dropoff_input_present", False),
                protocol={"errors": info.errors},
                last_checked=None,
                status_code=None,
            )
            debug_log_model(shipment, "after tracking")
            date_iso = shipment.tracking.delivery_date
            opts = shipment.tracking.delivery_options
            errors = shipment.tracking.protocol.get("errors", [])

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
                code, carrier_zip, carrier_location, carrier_highlight, selenium_headless, timeout
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
            logger.debug(
                f"Finished processing tracking code: %s (carrier: %s) [run_id=%s]", code, carrier, shipment.run_id
            )


def get_cli_defaults(config: dict) -> dict:
    """
    Extracts CLI default values from the loaded config dict in a single place.
    Returns a dict of defaults for CLI arguments.
    """
    mailboxes = config.get("mailboxes", [])
    weeks_default = mailboxes[0]["lookback_weeks"] if mailboxes and "lookback_weeks" in mailboxes[0] else None
    carrier_configs = config.get("carrier_configs", {})
    dhl_cfg = carrier_configs.get("DHL", {})
    return {
        "weeks": weeks_default,
        "zip_code": dhl_cfg.get("zip"),
        "custom_location": dhl_cfg.get("reroute_location"),
        "highlight_only": dhl_cfg.get("highlight_only", True),
        "selenium_headless": dhl_cfg.get("selenium_headless", True),
        "timeout": dhl_cfg.get("timeout", 20),
    }


def parse_cli_args(defaults: dict) -> argparse.Namespace:
    """
    Parses CLI arguments for the DHL rerouter, using provided defaults.
    Returns the parsed argparse.Namespace.
    """
    p = argparse.ArgumentParser()
    p.add_argument(
        "--weeks",
        type=int,
        help=f"Override lookback period (weeks back to search emails; overrides config if set) [default: {defaults['weeks']}]",
    )
    p.add_argument(
        "--zip",
        dest="zip_code",
        required=False,
        help=f"Postal code for DHL tracking page (overrides config if set) [default: {defaults['zip_code']}]",
    )
    p.add_argument(
        "--location",
        dest="custom_location",
        required=False,
        help=f"Custom drop‑off location text (overrides config if set) [default: {defaults['custom_location']}]",
    )
    p.set_defaults(**defaults)
    p.add_argument(
        "--highlight-only",
        action="store_true",
        help=f"Highlight only, do not click confirm (overrides config) [default: {defaults['highlight_only']}]",
    )
    p.add_argument(
        "--selenium-headless",
        action="store_true",
        help=f"Run Selenium in headless mode (overrides config) [default: {defaults['selenium_headless']}]",
    )
    p.add_argument(
        "--timeout",
        type=int,
        help=f"Timeout for Selenium waits (overrides config) [default: {defaults['timeout']}]",
    )
    return p.parse_args()


def validate_cli_args(args: argparse.Namespace) -> None:
    """
    Validates required CLI arguments and raises ValueError with clear message if missing.
    """
    if not args.zip_code:
        raise ValueError("A zip code must be provided via --zip or config.yaml under carriers:DHL:zip")
    if not args.custom_location:
        raise ValueError("A reroute location must be provided via --location or config.yaml under carriers:DHL:reroute_location")
    if args.weeks is None:
        raise ValueError("A lookback period must be provided via --weeks or config.yaml under email:lookback_weeks")


def main() -> None:
    """
    Entry point for DHL rerouter automation. Loads config and sets CLI defaults
    based on the new multi-mailbox structure. Carrier config logic is preserved.
    """
    config = load_config()
    defaults = get_cli_defaults(config)
    args = parse_cli_args(defaults)

    validate_cli_args(args)
    run(
        args.weeks,
        args.zip_code,
        args.custom_location,
        args.highlight_only,
        args.selenium_headless,
        args.timeout,
        config,
    )


if __name__ == "__main__":
    main()
