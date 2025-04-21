# dhl_rerouter_poc/main.py

import argparse
from .email_client        import ImapEmailClient
from .parser              import extract_tracking_codes
from .calendar_checker    import should_reroute
from .reroute_checker     import check_reroute_availability
from .reroute_executor    import reroute_shipment
from .config              import load_config

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

            # skip non‑DHL carriers
            if carrier != "DHL":
                print("  → skipping non‑DHL carrier")
                continue

            # scrape DHL page
            info = check_reroute_availability(code, zip_code, timeout=timeout)
            date_iso = info.get("delivery_date")
            opts     = info.get("delivery_options", [])
            errors   = info.get("protocol", {}).get("errors", [])

            # debug: show any protocol errors
            if errors:
                print(f"  ⚠️ encountered errors: {errors}")

            # calendar-based decision
            if not date_iso:
                print("  → no delivery_date parsed; skipping calendar check")
                continue
            print(f"  → checking calendar for delivery_date={date_iso}")
            should = should_reroute(code, date_iso, config)
            print(f"  → should_reroute returned {should}")
            if not should:
                print(f"  → skipped by calendar (delivery_date={date_iso})")
                continue

            # availability check
            if not opts:
                print("  → no reroute options available")
                continue
            print(f"  → available options: {opts}")

            # execute reroute
            print(f"  → performing reroute (highlight_only={highlight_only})")
            success = reroute_shipment(code, zip_code, custom_location, highlight_only, selenium_headless, timeout)
            print(f"  → reroute {'✅' if success else '❌'}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--weeks", type=int,
        help="Override lookback period (weeks back to search emails; overrides config if set)"
    )
    p.add_argument(
        "--zip", dest="zip_code", required=False,
        help="Postal code for DHL tracking page (overrides config if set)"
    )
    p.add_argument(
        "--location", dest="custom_location", required=False,
        help="Custom drop‑off location text (overrides config if set)"
    )
    config = load_config()
    # Set argparse defaults from config
    p.set_defaults(
        weeks=config.get("email", {}).get("lookback_weeks"),
        zip_code=config.get("dhl", {}).get("zip"),
        custom_location=config.get("dhl", {}).get("reroute_location"),
        highlight_only=config.get("dhl", {}).get("highlight_only", True),
        selenium_headless=config.get("dhl", {}).get("selenium_headless", False),
        timeout=config.get("dhl", {}).get("timeout", 20)
    )
    p.add_argument(
        "--highlight-only", action="store_true", help="Highlight only, do not click confirm (overrides config)"
    )
    p.add_argument(
        "--selenium-headless", action="store_true", help="Run Selenium in headless mode (overrides config)"
    )
    p.add_argument(
        "--timeout", type=int, help="Timeout for Selenium waits (overrides config)"
    )
    args = p.parse_args()
    # CLI always takes precedence if explicitly set
    highlight_only = args.highlight_only if 'highlight_only' in args else config.get("dhl", {}).get("highlight_only", True)
    selenium_headless = args.selenium_headless if 'selenium_headless' in args else config.get("dhl", {}).get("selenium_headless", False)
    timeout = args.timeout if args.timeout is not None else config.get("dhl", {}).get("timeout", 20)
    # Validate required parameters
    if not args.zip_code:
        raise ValueError("A zip code must be provided via --zip or config.yaml under dhl:zip")
    if not args.custom_location:
        raise ValueError("A reroute location must be provided via --location or config.yaml under dhl:reroute_location")
    if args.weeks is None:
        raise ValueError("A lookback period must be provided via --weeks or config.yaml under email:lookback_weeks")
    run(args.weeks, args.zip_code, args.custom_location, highlight_only, selenium_headless, timeout)
