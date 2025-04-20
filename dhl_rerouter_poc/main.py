# dhl_rerouter_poc/main.py

import argparse
from .email_client        import ImapEmailClient
from .parser              import extract_tracking_codes
from .calendar_checker    import should_reroute
from .reroute_checker     import check_reroute_availability
from .reroute_executor    import reroute_shipment
from .config              import load_config

def run(weeks: int = None, zip_code: str = None, custom_location: str = None):
    client = ImapEmailClient()
    if weeks:
        client.lookback = weeks
    bodies = client.fetch_messages()

    seen = set()
    for body in bodies:
        codes = extract_tracking_codes(body)
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
            info = check_reroute_availability(code, zip_code)
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
            should = should_reroute(code, date_iso)
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
            dhl_cfg = load_config().get("dhl", {})
            print(f"  → performing reroute (highlight_only={dhl_cfg.get('highlight_only',True)})")
            success = reroute_shipment(code, zip_code, custom_location)
            print(f"  → reroute {'✅' if success else '❌'}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--weeks", type=int,
        help="Override lookback period (weeks back to search emails)"
    )
    p.add_argument(
        "--zip", dest="zip_code", required=True,
        help="Postal code for DHL tracking page"
    )
    p.add_argument(
        "--location", dest="custom_location", required=True,
        help="Custom drop‑off location text"
    )
    args = p.parse_args()
    run(args.weeks, args.zip_code, args.custom_location)
