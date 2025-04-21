# dhl_rerouter_poc/main.py

import argparse
from .email_client        import ImapEmailClient
from .parser              import extract_tracking_codes
from .calendar_checker    import should_reroute
from .reroute_checker     import check_reroute_availability
from .reroute_executor    import reroute_shipment
from .config              import load_config
from .workflow_data_model import (
    ShipmentLifecycle,
    TransportProviderInfo,
    ConsignmentNotification,
    ShipmentTrackingInfo,
    RecipientAvailability,
    DeliveryInterventionResult,
)

def run(weeks: int = None, zip_code: str = None, custom_location: str = None, highlight_only: bool = True, selenium_headless: bool = False, timeout: int = 20, config: dict = None):
    client = ImapEmailClient(config["email"])
    if weeks:
        client.lookback = weeks
    bodies = client.fetch_messages()

    seen = set()
    for body in bodies:
        codes = extract_tracking_codes(body, config["tracking_patterns"])
        for code, carrier in sorted(codes.items()):
            if code in seen:
                continue
            seen.add(code)
            print(f"{code} ({carrier})")

            # --- Build ShipmentLifecycle context ---
            shipment = ShipmentLifecycle(
                provider=TransportProviderInfo(name=carrier, tracking_number=code),
                notification=ConsignmentNotification(
                    normalized_body=body[:4096],
                    body_truncated=len(body) > 4096,
                    # Optionally fill subject/sender/received_at if available from client
                ),
            )

            # skip unsupported carriers (model-driven)
            if not shipment.provider.is_supported():
                print(f"  → skipping unsupported carrier: {carrier}")
                continue

            # --- Tracking info ---
            info = check_reroute_availability(code, zip_code, timeout=timeout)
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
            date_iso = shipment.tracking.delivery_date
            opts     = shipment.tracking.delivery_options
            errors   = shipment.tracking.protocol.get("errors", [])

            # debug: show any protocol errors
            if errors:
                print(f"  ⚠️ encountered errors: {errors}")

            # --- Calendar-based decision ---
            if not date_iso:
                print("  → no delivery_date parsed; skipping calendar check")
                continue
            print(f"  → checking calendar for delivery_date={date_iso}")
            should = should_reroute(code, date_iso, config)
            shipment.recipient_availability = RecipientAvailability(
                delivery_date=date_iso,
                is_away=not should,
                overlapping_absences=[],  # Could be filled by should_reroute in future
                sources_checked=[],
            )
            print(f"  → should_reroute returned {should}")
            if not should:
                print(f"  → skipped by calendar (delivery_date={date_iso})")
                continue

            # --- Availability check ---
            if not opts:
                print("  → no reroute options available")
                continue
            print(f"  → available options: {opts}")

            # --- Execute reroute ---
            print(f"  → performing reroute (highlight_only={highlight_only})")
            success = reroute_shipment(code, zip_code, custom_location, highlight_only, selenium_headless, timeout)
            shipment.intervention = DeliveryInterventionResult(
                attempted=True,
                success=success,
                error=None if success else "reroute failed",
                timestamp=None,
                attempts=1,
                status_code=200 if success else 500,
                detail=None,
            )
            print(f"  → reroute {'✅' if success else '❌'}")

def main():
    config = load_config()
    weeks_default = config.get("email", {}).get("lookback_weeks")
    zip_default = config.get("dhl", {}).get("zip")
    location_default = config.get("dhl", {}).get("reroute_location")
    highlight_default = config.get("dhl", {}).get("highlight_only", True)
    selenium_headless_default = config.get("dhl", {}).get("selenium_headless", False)
    timeout_default = config.get("dhl", {}).get("timeout", 20)

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
        raise ValueError("A zip code must be provided via --zip or config.yaml under dhl:zip")
    if not args.custom_location:
        raise ValueError("A reroute location must be provided via --location or config.yaml under dhl:reroute_location")
    if args.weeks is None:
        raise ValueError("A lookback period must be provided via --weeks or config.yaml under email:lookback_weeks")
    run(args.weeks, args.zip_code, args.custom_location, highlight_only, selenium_headless, timeout)

if __name__ == "__main__":
    main()
