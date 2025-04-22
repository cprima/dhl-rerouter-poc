"""
DHL Action test: Populate ShipmentTrackingInfo from DHL tracking page using Selenium POM.
This test is an integration/action test, not a unit test.
Test data is loaded from tracking_page_scenarios_dhl.yaml and is specific to carrier DHL.
"""
import pytest
from datetime import datetime
from dhl_rerouter_poc.workflow_data_model import ShipmentTrackingInfo

import yaml
import pytest
from datetime import datetime
from dhl_rerouter_poc.workflow_data_model import ShipmentTrackingInfo

def load_tracking_page_scenarios_dhl():
    with open("tests/tracking_page_scenarios_dhl.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.mark.parametrize(
    "scenario",
    load_tracking_page_scenarios_dhl(),
    ids=lambda scenario: scenario["tracking_number"]
)
def test_populate_shipment_tracking_info_dhl(scenario):
    from selenium_utils.webdriver_factory import create_chrome_driver
    from dhl_rerouter_poc.carriers.dhl.pages import DHLTrackingPage
    from dhl_rerouter_poc.carriers.dhl.locators import DHLTrackingLocators

    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("dhl_test")

    assert scenario["carrier"] == "DHL", "Test scenario carrier mismatch: expected 'DHL'"
    tracking_number = scenario["tracking_number"]
    zip_code = scenario["zip_code"]
    logger.info(f"Creating Chrome driver (headless=False)...")
    driver = create_chrome_driver(headless=False)
    try:
        logger.info(f"Opening DHL tracking page for tracking_number={tracking_number}, zip_code={zip_code}")
        page = DHLTrackingPage(driver)
        page.open(tracking_number, zip_code)
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        wait = WebDriverWait(driver, 60)
        logger.info("Waiting for shipment content div to be visible...")
        wait.until(EC.visibility_of_element_located(
            DHLTrackingLocators.shipment_content_div(tracking_number)
        ))
        logger.info("Shipment content div is visible.")
        title = driver.title
        logger.info(f"Page title: {title}")
        assert ("Track" in title) or ("Trace" in title)

        # Extract DELIVERY_STATUS and DELIVERY_DATE using locators
        try:
            logger.info("Attempting to locate DELIVERY_STATUS element...")
            status_el = driver.find_element(*DHLTrackingLocators.DELIVERY_STATUS)
            logger.info(f"DELIVERY_STATUS element found: '{status_el.text.strip()}'")
            logger.info("Attempting to locate DELIVERY_DATE element...")
            date_el = driver.find_element(*DHLTrackingLocators.DELIVERY_DATE)
            raw_date = date_el.text.strip()
            logger.info(f"DELIVERY_DATE <time> element found: '{raw_date}'")
            from dhl_rerouter_poc.utils import parse_dhl_date
            parsed_date = parse_dhl_date(raw_date)
            logger.info(f"Parsed delivery date: '{parsed_date}'")
            status_text = status_el.text.strip()
            delivery_status = status_text
            status = ShipmentTrackingInfo.set_status(delivery_status, parsed_date)
            delivered = status == "delivered"
            # Assert delivered and delivery_date from scenario if provided
            def _should_assert(val):
                return val is not None and val != "TODO"
            if _should_assert(scenario.get("expected_delivered")):
                logger.info(f"Asserting delivered: expected={scenario['expected_delivered']} actual={delivered}")
                assert delivered == scenario["expected_delivered"]
            if _should_assert(scenario.get("expected_delivery_date")):
                logger.info(f"Asserting delivery_date: expected={scenario['expected_delivery_date']} actual={parsed_date}")
                assert parsed_date == scenario["expected_delivery_date"]

            # Extract delivered-to (signer) only for delivered shipments
            if scenario.get("expected_delivered_to") is None:
                delivered_to = None
                logger.info("No delivered-to element expected for undelivered shipment.")
            else:
                delivered_to_el = DHLTrackingLocators.get_delivered_to(driver, logger, delivered=(status=="delivered"))
                assert delivered_to_el is not None, "Delivered-to element not found by any selector"
                delivered_to = delivered_to_el.text.strip()
                logger.info(f"Delivered-to element found: '{delivered_to}'")
                logger.info(f"Asserting delivered_to: expected={scenario['expected_delivered_to']} actual={delivered_to}")
                assert delivered_to == scenario["expected_delivered_to"]

            # Extract delivery options
            options = [el.text.strip() for el in driver.find_elements(*DHLTrackingLocators.DELIVERY_OPTIONS)]
            logger.info(f"Delivery options: {options}")

            # Extract shipment history
            history = [el.text.strip() for el in driver.find_elements(*DHLTrackingLocators.SHIPMENT_HISTORY_ENTRY)]
            logger.info(f"Shipment history: {history}")

            # Check for custom dropoff input
            custom_dropoff_present = bool(driver.find_elements(*DHLTrackingLocators.CUSTOM_DROPOFF_INPUT))
            logger.info(f"Custom dropoff input present: {custom_dropoff_present}")

            # Build protocol for traceability
            protocol = {
                "raw_status": status_text,
                "raw_date": raw_date,
                "delivered_to": delivered_to,
                "options": options,
                "history": history,
            }

            # Populate ShipmentTrackingInfo using the model's business logic
            info = ShipmentTrackingInfo.from_extracted_data(
                delivery_status=delivery_status,
                parsed_date=parsed_date,
                delivery_options=options,
                shipment_history=history,
                custom_dropoff_input_present=custom_dropoff_present,
                protocol=protocol,
                last_checked=datetime.now().isoformat(timespec="seconds"),
                status_code=200,
            )
            logger.info(f"Populated ShipmentTrackingInfo: {info.model_dump_json(indent=2)}")
            # Assert against expected values from scenario
            def _should_assert(val):
                return val is not None and val != "TODO"

            if _should_assert(scenario.get("expected_status")):
                logger.info(f"Asserting status: expected={scenario['expected_status']} actual={info.status}")
                assert info.status == scenario["expected_status"]
            if _should_assert(scenario.get("expected_delivered")):
                logger.info(f"Asserting delivered: expected={scenario['expected_delivered']} actual={info.delivered}")
                assert info.delivered == scenario["expected_delivered"]
            # Only assert delivery_date if status is 'delivered' and expected value is not TODO
            if info.status == "delivered" and _should_assert(scenario.get("expected_delivery_date")):
                logger.info(f"Asserting delivery_date: expected={scenario['expected_delivery_date']} actual={info.delivery_date}")
                assert info.delivery_date == scenario["expected_delivery_date"]
            elif info.status != "delivered":
                logger.info(f"Skipping delivery_date assertion because status is not 'delivered' (actual: {info.status})")
            if _should_assert(scenario.get("expected_delivery_status")):
                logger.info(f"Asserting delivery_status: expected={scenario['expected_delivery_status']} actual={info.delivery_status}")
                assert info.delivery_status == scenario["expected_delivery_status"]
            # delivered_to assertion already handled above; no further assertion needed here
            # Optionally assert other fields as needed

        except Exception as e:
            logger.error(f"Could not find status/date elements: {e}")
            logger.info("Current page source saved to dhl_debug.html")
            with open("dhl_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise
    finally:
        logger.info("Test complete. Keeping browser open for 30 seconds for manual inspection...")
        import time
        time.sleep(30)
        logger.info("Quitting driver.")
        driver.quit()
