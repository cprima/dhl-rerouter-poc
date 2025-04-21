# dhl_rerouter_poc/reroute_checker.py

import time
import logging
from datetime import datetime, timezone
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .selectors_dhlde import (
    DELIVERY_DATE,
    DELIVERED_TEXTS,
    DELIVERY_TOGGLE,
    SHIPMENT_HISTORY_ENTRY,
    CUSTOM_DROPOFF_INPUT,
    delivery_status_selector,
    ALLOWED_DELIVERY_OPTION_KEYS,
)
from .utils import parse_dhl_date

import logging
logger = logging.getLogger(__name__)

# DEPRECATED: Use DHLCarrier.check_reroute_availability instead.
from dhl_rerouter_poc.carriers.dhl import DHLCarrier

def check_reroute_availability(tracking_number: str, zip_code: str, timeout: int = 20, run_id: str | None = None) -> dict:
    """
    Deprecated. Use DHLCarrier().check_reroute_availability instead.
    """
    if run_id:
        logger.info("Going to check reroute availability (wrapper) for %s [run_id=%s]", tracking_number, run_id)
    else:
        logger.info("Going to check reroute availability (wrapper) for %s", tracking_number)
    result = DHLCarrier().check_reroute_availability(tracking_number, zip_code, timeout, run_id=run_id)
    if run_id:
        logger.debug("Finished check reroute availability (wrapper) for %s [run_id=%s]", tracking_number, run_id)
    else:
        logger.debug("Finished check reroute availability (wrapper) for %s", tracking_number)
    return result
