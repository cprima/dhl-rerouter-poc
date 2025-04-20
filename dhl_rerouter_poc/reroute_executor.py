# dhl_rerouter_poc/reroute_executor.py

import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config import load_config
from .selectors_dhlde import DELIVERY_TOGGLE, DELIVERY_OPTIONS, CUSTOM_DROPOFF_INPUT
from .utils import blink_element

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# XPath for the confirmation button
CONFIRM_BUTTON_XPATH = "//button[text()='Confirm']"

def reroute_shipment(
    tracking_number: str,
    zip_code: str,
    custom_location: str,
    timeout: int = 20
) -> bool:
    """
    Navigate DHL page, always perform steps 1–4, then in step 5 (confirm button)
    honor highlight_only: if True, only highlight; if False, click.
    """
    cfg = load_config().get("dhl", {})
    highlight_only = cfg.get("highlight_only", True)
    headless      = cfg.get("selenium_headless", False)

    url = (
        f"https://www.dhl.de/en/privatkunden/"
        f"pakete-empfangen/verfolgen.html?"
        f"piececode={tracking_number}&zip={zip_code}&lang=en"
    )

    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--lang=en")
    options.add_argument("--incognito")

    driver = uc.Chrome(options=options)
    wait   = WebDriverWait(driver, timeout)

    try:
        LOG.info("Loading DHL page for %s...", tracking_number)
        driver.get(url)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "article[class*='shipment']")))

        # Step 1: expand delivery options (always click)
        LOG.info("Expanding delivery options...")
        toggle = wait.until(EC.element_to_be_clickable((By.XPATH, DELIVERY_TOGGLE)))
        driver.execute_script("arguments[0].scrollIntoView(true)", toggle)
        toggle.click()
        LOG.info("Clicked delivery options toggle.")
        time.sleep(1)

        # Step 2: select drop‑off location (always click)
        LOG.info("Selecting drop-off location option...")
        # target the PREFERRED_LOCATION data-name
        el = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@data-name='PREFERRED_LOCATION']")))
        driver.execute_script("arguments[0].scrollIntoView(true)", el)
        el.click()
        LOG.info("Clicked PREFERRED_LOCATION option.")
        time.sleep(1)

        # Step 3: wait for form
        LOG.info("Waiting for drop-off form...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
        LOG.info("Drop-off form loaded.")

        # Step 4: enter custom drop‑off text with offset scroll
        LOG.info("Entering custom drop-off text: %s", custom_location)
        inp = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, CUSTOM_DROPOFF_INPUT)))
        # scroll so the input sits 100px below the top of the viewport
        driver.execute_script("""
            const el = arguments[0];
            const rect = el.getBoundingClientRect();
            window.scrollBy({ top: rect.top - 100, left: 0, behavior: 'smooth' });
        """, inp)
        # optionally highlight it
        driver.execute_script("arguments[0].style.border='3px solid blue'", inp)
        time.sleep(0.5)
        inp.clear()
        inp.send_keys(custom_location)
        LOG.info("Custom drop-off text entered.")
        time.sleep(1)

        # Step 5: click the consent checkbox (always)
        LOG.info("Clicking consent checkbox...")
        checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox']")
        driver.execute_script("arguments[0].scrollIntoView(true)", checkbox)
        time.sleep(0.5)
        checkbox.click()
        LOG.info("Checkbox clicked.")

        # Step 6: blink highlight the Confirm button, then click if allowed
        LOG.info("Processing confirmation button (highlight_only=%s)...", highlight_only)
        confirm = wait.until(EC.presence_of_element_located((By.XPATH, CONFIRM_BUTTON_XPATH)))
        # scroll into view with offset
        driver.execute_script("""
            const rect = arguments[0].getBoundingClientRect();
            window.scrollBy({ top: rect.top - 100, left: 0, behavior: 'smooth' });
        """, confirm)

        # blink effect
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
