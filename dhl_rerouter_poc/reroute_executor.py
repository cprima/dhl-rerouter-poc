# dhl_rerouter_poc/reroute_executor.py

import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .selectors_dhlde import DELIVERY_TOGGLE, DELIVERY_OPTIONS, CUSTOM_DROPOFF_INPUT
from .utils import blink_element

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# XPath for the confirmation button
CONFIRM_BUTTON_XPATH = "//button[text()='Confirm']"

# DEPRECATED: Use DHLCarrier.reroute_shipment instead.
from dhl_rerouter_poc.carriers.dhl import DHLCarrier

def reroute_shipment(
    tracking_number: str,
    zip_code: str,
    custom_location: str,
    highlight_only: bool = True,
    selenium_headless: bool = False,
    timeout: int = 20,
    run_id: str | None = None
) -> bool:
    """
    Deprecated. Use DHLCarrier().reroute_shipment instead.
    """
    if run_id:
        logger.info("Going to reroute shipment (wrapper) for %s [run_id=%s]", tracking_number, run_id)
    else:
        logger.info("Going to reroute shipment (wrapper) for %s", tracking_number)
    result = DHLCarrier().reroute_shipment(
        tracking_number,
        zip_code,
        custom_location,
        highlight_only,
        selenium_headless,
        timeout,
        run_id=run_id
    )
    if run_id:
        logger.debug("Finished reroute shipment (wrapper) for %s [run_id=%s]", tracking_number, run_id)
    else:
        logger.debug("Finished reroute shipment (wrapper) for %s", tracking_number)
    return result
