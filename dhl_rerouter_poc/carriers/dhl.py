"""
DHLCarrier: Implements CarrierBase for DHL-specific logic.
"""
import logging
from datetime import datetime, timezone
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dhl_rerouter_poc.carriers.base import CarrierBase
from dhl_rerouter_poc.selectors_dhlde import (
    DELIVERY_DATE,
    DELIVERED_TEXTS,
    DELIVERY_TOGGLE,
    SHIPMENT_HISTORY_ENTRY,
    CUSTOM_DROPOFF_INPUT,
    delivery_status_selector,
    ALLOWED_DELIVERY_OPTION_KEYS,
)
from dhl_rerouter_poc.utils import parse_dhl_date, blink_element

LOG = logging.getLogger(__name__)

class DHLCarrier(CarrierBase):
    carrier_name: str = "DHL"

    def check_reroute_availability(
        self,
        tracking_number: str,
        zip_code: str,
        timeout: int = 20,
        selenium_headless: bool = False,
        run_id: str | None = None
    ) -> dict:
        """
        Check if reroute is available for a shipment using Selenium.
        Honors headless mode from config.
        """
        if run_id:
            LOG.info("Going to check reroute availability for %s [run_id=%s]", tracking_number, run_id)
        else:
            LOG.info("Going to check reroute availability for %s", tracking_number)
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
        if selenium_headless:
            options.add_argument("--headless")
            LOG.info("Launching Selenium in headless mode for check_reroute_availability.")
        else:
            LOG.info("Launching Selenium in visible mode for check_reroute_availability.")
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
        if run_id:
            LOG.debug("Finished checking reroute availability for %s [run_id=%s]", tracking_number, run_id)
        else:
            LOG.debug("Finished checking reroute availability for %s", tracking_number)
        return result

    def reroute_shipment(
        self,
        tracking_number: str,
        zip_code: str,
        custom_location: str,
        highlight_only: bool = True,
        selenium_headless: bool = False,
        timeout: int = 20,
        run_id: str | None = None
    ) -> bool:
        """
        Execute the shipment rerouting process using Selenium.

        Args:
            tracking_number (str): The tracking number of the shipment.
            zip_code (str): The zip code of the shipment.
            custom_location (str): The custom location for the shipment.
            highlight_only (bool, optional): Whether to only highlight the confirm button. Defaults to True.
            selenium_headless (bool, optional): Whether to run Selenium in headless mode. Defaults to False.
            timeout (int, optional): The timeout for the Selenium driver. Defaults to 20.

        Returns:
            bool: Whether the rerouting process was successful.
        """
        url = (
            f"https://www.dhl.de/en/privatkunden/"
            f"pakete-empfangen/verfolgen.html?"
            f"piececode={tracking_number}&zip={zip_code}&lang=en"
        )
        if run_id:
            LOG.info("Going to reroute shipment for %s [run_id=%s]", tracking_number, run_id)
        else:
            LOG.info("Going to reroute shipment for %s", tracking_number)
        options = uc.ChromeOptions()
        if selenium_headless:
            options.add_argument("--headless")
            LOG.info("Launching Selenium in headless mode for reroute_shipment.")
        else:
            LOG.info("Launching Selenium in visible mode for reroute_shipment.")
        options.add_argument("--lang=en")
        options.add_argument("--incognito")
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, timeout)
        try:
            LOG.info("Loading DHL page for %s...", tracking_number)
            driver.get(url)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "article[class*='shipment']")))
            # Step 1: expand delivery options
            LOG.info("Expanding delivery options...")
            toggle = wait.until(EC.element_to_be_clickable((By.XPATH, DELIVERY_TOGGLE)))
            driver.execute_script("arguments[0].scrollIntoView(true)", toggle)
            toggle.click()
            LOG.info("Clicked delivery options toggle.")
            time.sleep(1)
            # Step 2: select drop‑off location
            LOG.info("Selecting drop-off location option...")
            el = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@data-name='PREFERRED_LOCATION']")))
            driver.execute_script("arguments[0].scrollIntoView(true)", el)
            el.click()
            LOG.info("Clicked PREFERRED_LOCATION option.")
            time.sleep(1)
            # Step 3: wait for form
            LOG.info("Waiting for drop-off form...")
            wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
            LOG.info("Drop-off form loaded.")
            # Step 4: enter custom drop‑off text
            LOG.info("Entering custom drop-off text: %s", custom_location)
            inp = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, CUSTOM_DROPOFF_INPUT)))
            driver.execute_script("""
                const el = arguments[0];
                const rect = el.getBoundingClientRect();
                window.scrollBy({ top: rect.top - 100, left: 0, behavior: 'smooth' });
            """, inp)
            driver.execute_script("arguments[0].style.border='3px solid blue'", inp)
            time.sleep(0.5)
            inp.clear()
            inp.send_keys(custom_location)
            LOG.info("Custom drop-off text entered.")
            time.sleep(1)
            # Step 5: click the consent checkbox
            LOG.info("Clicking consent checkbox...")
            checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox']")
            driver.execute_script("arguments[0].scrollIntoView(true)", checkbox)
            time.sleep(0.5)
            checkbox.click()
            LOG.info("Checkbox clicked.")
            # Step 6: blink highlight the Confirm button, then click if allowed
            LOG.info("Processing confirmation button (highlight_only=%s)...", highlight_only)
            CONFIRM_BUTTON_XPATH = "//button[text()='Confirm']"
            confirm = wait.until(EC.presence_of_element_located((By.XPATH, CONFIRM_BUTTON_XPATH)))
            driver.execute_script("""
                const rect = arguments[0].getBoundingClientRect();
                window.scrollBy({ top: rect.top - 100, left: 0, behavior: 'smooth' });
            """, confirm)
            blink_element(driver, confirm, times=5, color="purple", width=10, interval=0.3)
            if not highlight_only:
                confirm.click()
                LOG.info("Clicked Confirm button.")
            else:
                LOG.info("Highlighted Confirm button, not clicked.")
                time.sleep(5)
            return True
        except Exception as e:
            LOG.error("Reroute executor failed for %s: %s", tracking_number, e)
            return False
        finally:
            driver.quit()
        if run_id:
            LOG.debug("Finished reroute shipment for %s [run_id=%s]", tracking_number, run_id)
        else:
            LOG.debug("Finished reroute shipment for %s", tracking_number)
