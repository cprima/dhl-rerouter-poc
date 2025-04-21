# dhl_rerouter_poc/reroute_executor.py

import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .selectors_dhlde import DELIVERY_TOGGLE, DELIVERY_OPTIONS, CUSTOM_DROPOFF_INPUT
from .utils import blink_element

LOG = logging.getLogger(__name__)
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
    timeout: int = 20
) -> bool:
    """
    Deprecated. Use DHLCarrier().reroute_shipment instead.
    """
    return DHLCarrier().reroute_shipment(
        tracking_number,
        zip_code,
        custom_location,
        highlight_only,
        selenium_headless,
        timeout
    )
