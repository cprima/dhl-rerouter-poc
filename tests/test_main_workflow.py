import pytest
from unittest.mock import patch
from dhl_rerouter_poc import main, config
from test_scenarios_model import RerouteTestScenario, load_scenarios
from contextlib import ExitStack

@pytest.fixture(scope="session")
def test_config():
    return config.load_config()

@pytest.mark.parametrize(
    "scenario",
    load_scenarios("tests/reroute_scenarios.yaml"),
    ids=lambda scenario: scenario.tracking_number
)
def test_tracking_scenarios(scenario: RerouteTestScenario, test_config):
    """
    Table-driven test for main.run():
    - tracking_number: code to test
    - reroute_available: if reroute_checker should say reroutable
    - calendar_away: if calendar_checker should say user is away
    - expected_reroute: if reroute_shipment should be called
    """
    test_email = [f"Your DHL tracking number is {scenario.tracking_number}"]
    def fake_check_reroute_availability(code, zip_code, timeout=20, selenium_headless=True):
        if scenario.reroute_available:
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
    patchers = [
        patch("dhl_rerouter_poc.email_client.ImapEmailClient.fetch_messages", return_value=test_email),
        patch("dhl_rerouter_poc.reroute_checker.check_reroute_availability", side_effect=fake_check_reroute_availability),
        patch("dhl_rerouter_poc.calendar_checker.should_reroute", return_value=scenario.calendar_away),
    ]
    if not scenario.expected_reroute:
        patchers.append(patch("dhl_rerouter_poc.main.reroute_shipment", return_value=True))
    with ExitStack() as stack:
        mocks = [stack.enter_context(p) for p in patchers]
        main.run(
            weeks=test_config["email"]["lookback_weeks"],
            zip_code=test_config["carrier_configs"]["DHL"]["zip"],
            custom_location=test_config["carrier_configs"]["DHL"]["reroute_location"],
            highlight_only=test_config["carrier_configs"]["DHL"].get("highlight_only", True),
            selenium_headless=test_config["carrier_configs"]["DHL"].get("selenium_headless", True),
            timeout=test_config["carrier_configs"]["DHL"].get("timeout", 20),
            config=test_config
        )
        if scenario.expected_reroute:
            # Optionally assert side effects, logs, or UI changes here
            pass
        else:
            mocks[-1].assert_not_called()
