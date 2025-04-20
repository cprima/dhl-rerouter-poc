# dhl_rerouter_poc/main.py

import argparse
from .email_client        import ImapEmailClient
from .parser              import extract_tracking_codes
from .calendar_checker    import should_reroute
from .reroute_checker     import check_reroute_availability
from .reroute_executor    import reroute_shipment

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

            if not should_reroute(code):
                print("  → skipped by calendar")
                continue

            info = check_reroute_availability(code, zip_code)
            opts = info.get("delivery_options", [])
            if not opts:
                print("  → no reroute options available")
                continue

            success = reroute_shipment(code, zip_code, custom_location)
            print(f"  → reroute {'✅' if success else '❌'}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--weeks",    type=int,       help="Override lookback period")
    p.add_argument("--zip",      dest="zip_code", required=True, help="Postal code for DHL")
    p.add_argument("--location", dest="custom_location", required=True, help="Custom drop‑off location")
    args = p.parse_args()
    run(args.weeks, args.zip_code, args.custom_location)
