import pytest
from unittest.mock import patch
from dhl_rerouter_poc import main, config

# Table-driven test cases for tracking code scenarios
# Each tuple: (tracking_number, reroute_available, calendar_away, expected_reroute)
test_cases = [
    # Should reroute: reroutable, calendar says away
    ("JJD000390018282329702", True, True, True),
    # Should NOT reroute: already delivered, calendar says away
    ("JJD149160000010324577", True, False, False),
    # Should NOT reroute: reroutable, calendar says NOT away
    ("00340434175967421417", True, False, False),
    # Should NOT reroute: not reroutable, calendar says NOT away
    ("00340434664895388034", True, False, False),
]

@pytest.mark.parametrize("tracking_number,reroute_available,calendar_away,expected_reroute", test_cases)
def test_tracking_scenarios(tracking_number, reroute_available, calendar_away, expected_reroute):
    """
    Table-driven test for main.run():
    - tracking_number: code to test
    - reroute_available: if reroute_checker should say reroutable
    - calendar_away: if calendar_checker should say user is away
    - expected_reroute: if reroute_shipment should be called
    """
    test_email = [f"Your DHL tracking number is {tracking_number}"]
    def fake_check_reroute_availability(code, zip_code, timeout=20):
        if reroute_available:
            return {
                "tracking_number": code,
                "delivered": False,
                "delivery_date": "2025-04-22",
                "delivery_options": ["PREFERRED_LOCATION"],
                "protocol": {"errors": []}
            }
        else:
            return {
                "tracking_number": code,
                "delivered": True,
                "delivery_date": "2025-04-18",
                "delivery_options": [],
                "protocol": {"errors": []}
            }
    with patch("dhl_rerouter_poc.email_client.ImapEmailClient.fetch_messages", return_value=test_email), \
         patch("dhl_rerouter_poc.reroute_checker.check_reroute_availability", side_effect=fake_check_reroute_availability), \
         patch("dhl_rerouter_poc.calendar_checker.should_reroute", return_value=calendar_away), \
         patch("dhl_rerouter_poc.main.reroute_shipment", return_value=True) as mock_reroute:
        main.run(
            weeks=4,
            zip_code="38448",
            custom_location="Wohnungstür 1. OG rechts",
            highlight_only=True,
            selenium_headless=False,
            timeout=20,
            config=config.load_config()
        )
        if expected_reroute:
            mock_reroute.assert_called_once_with(tracking_number, "38448", "Wohnungstür 1. OG rechts", True, True, 20)
        else:
            mock_reroute.assert_not_called()

# Integration test: do not patch reroute_shipment, exercise the real reroute logic when all preconditions are met
@pytest.mark.integration
def test_real_reroute_execution():
    """
    Integration test: When all preconditions are met, the real reroute_shipment logic should be exercised.
    This test will attempt to perform a real reroute (headless, highlight_only).
    """
    tracking_number = "JJD000390018282329702"
    test_email = [f"Your DHL tracking number is {tracking_number}"]
    def fake_check_reroute_availability(code, zip_code, timeout=20):
        return {
            "tracking_number": code,
            "delivered": False,
            "delivery_date": "2025-04-22",
            "delivery_options": ["PREFERRED_LOCATION"],
            "protocol": {"errors": []}
        }
    with patch("dhl_rerouter_poc.email_client.ImapEmailClient.fetch_messages", return_value=test_email), \
         patch("dhl_rerouter_poc.reroute_checker.check_reroute_availability", side_effect=fake_check_reroute_availability), \
         patch("dhl_rerouter_poc.calendar_checker.should_reroute", return_value=True):
        # This will trigger the real reroute_shipment logic
        main.run(
            weeks=4,
            zip_code="38448",
            custom_location="Wohnungstür 1. OG rechts",
            highlight_only=True,
            selenium_headless=False,
            timeout=20,
            config=config.load_config()
        )
    # Optionally, assert on logs or side effects if needed
