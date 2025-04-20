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

LOG = logging.getLogger(__name__)

def check_reroute_availability(tracking_number: str, zip_code: str, timeout: int = 20) -> dict:
    """
    Scrapes DHL and returns a dict with:
      - tracking_number
      - delivered (bool)
      - delivery_date (ISO str or raw)
      - delivery_status (str or None)
      - delivery_options (list[str])
      - shipment_history (list[str])
      - custom_dropoff_input_present (bool)
      - protocol { timestamp, status, errors }
    """
    result = {
        "tracking_number": tracking_number,
        "delivered": False,
        "delivery_date": None,
        "delivery_status": None,
        "delivery_options": [],
        "shipment_history": [],
        "custom_dropoff_input_present": False,
        "protocol": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "errors": []
        }
    }

    url = (
        f"https://www.dhl.de/en/privatkunden/"
        f"pakete-empfangen/verfolgen.html?"
        f"piececode={tracking_number}&zip={zip_code}&lang=en"
    )

    options = uc.ChromeOptions()
    options.add_argument("--lang=en")
    options.add_argument("--incognito")
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, timeout)

    try:
        driver.get(url)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "article[class*='shipment']")))

        # shipment status
        try:
            by, sel = delivery_status_selector(tracking_number)
            result["delivery_status"] = driver.find_element(by, sel).text.strip()
        except Exception as e:
            result["protocol"]["errors"].append(f"delivery_status: {e}")

        # estimated delivery date (raw)
        raw_date = None
        try:
            raw_date = driver.find_element(By.XPATH, DELIVERY_DATE).text.strip()
            iso = parse_dhl_date(raw_date)
            if iso:
                result["delivery_date"] = iso
                LOG.debug("Parsed DHL date '%s' → %s", raw_date, iso)
            else:
                result["delivery_date"] = raw_date
                LOG.warning("Could not parse DHL date '%s'", raw_date)
        except Exception as e:
            result["protocol"]["errors"].append(f"delivery_date: {e}")

        # delivered?
        try:
            for el in driver.find_elements(By.XPATH, DELIVERED_TEXTS):
                txt = el.text.lower()
                if "delivered" in txt or "zustellt" in txt:
                    result["delivered"] = True
                    break
        except Exception as e:
            result["protocol"]["errors"].append(f"delivered_check: {e}")

        # available delivery options
        try:
            toggle = wait.until(EC.element_to_be_clickable((By.XPATH, DELIVERY_TOGGLE)))
            driver.execute_script("arguments[0].scrollIntoView(true)", toggle)
            time.sleep(1)
            toggle.click()
            time.sleep(1)

            items = driver.find_elements(By.CSS_SELECTOR, "div.verfuegen-container ul li[data-name]")
            for li in items:
                name = li.get_attribute("data-name")
                if name in ALLOWED_DELIVERY_OPTION_KEYS:
                    result["delivery_options"].append(name)
        except Exception as e:
            result["protocol"]["errors"].append(f"delivery_options: {e}")

        # shipment history
        try:
            for entry in driver.find_elements(By.CSS_SELECTOR, SHIPMENT_HISTORY_ENTRY):
                txt = entry.text.strip()
                if txt:
                    result["shipment_history"].append(txt)
        except Exception as e:
            result["protocol"]["errors"].append(f"shipment_history: {e}")

        # custom drop-off input
        try:
            driver.find_element(By.CSS_SELECTOR, CUSTOM_DROPOFF_INPUT)
            result["custom_dropoff_input_present"] = True
        except:
            result["custom_dropoff_input_present"] = False

    except Exception as e:
        result["protocol"]["status"] = "error"
        result["protocol"]["errors"].append(f"main_block: {e}")
    finally:
        driver.quit()

    return result
