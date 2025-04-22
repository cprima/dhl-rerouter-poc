"""
Page Object for DHL Tracking Page.
Encapsulates DHL page interactions using Selenium.
"""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .locators import DHLTrackingLocators
from typing import Optional

class DHLTrackingPage:
    def __init__(self, driver: WebDriver, timeout: int = 20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open(self, tracking_number: str, zip_code: str) -> None:
        url = (
            f"https://www.dhl.de/en/privatkunden/"
            f"pakete-empfangen/verfolgen.html?"
            f"piececode={tracking_number}&zip={zip_code}&lang=en"
        )
        self.driver.get(url)

    def get_delivery_status(self) -> Optional[str]:
        try:
            el = self.wait.until(EC.visibility_of_element_located(DHLTrackingLocators.DELIVERY_STATUS))
            return el.text.strip()
        except Exception:
            return None

    def get_delivery_date(self) -> Optional[str]:
        try:
            el = self.wait.until(EC.visibility_of_element_located(DHLTrackingLocators.DELIVERY_DATE))
            return el.text.strip()
        except Exception:
            return None

    def is_delivered(self) -> bool:
        try:
            elements = self.driver.find_elements(*DHLTrackingLocators.DELIVERED_TEXTS)
            return any("delivered" in el.text.lower() or "zustellt" in el.text.lower() for el in elements)
        except Exception:
            return False

    def expand_delivery_options(self) -> None:
        toggle = self.wait.until(EC.element_to_be_clickable(DHLTrackingLocators.DELIVERY_TOGGLE))
        toggle.click()

    def select_preferred_location(self) -> None:
        el = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@data-name='PREFERRED_LOCATION']")))
        el.click()

    def enter_custom_dropoff(self, text: str) -> None:
        inp = self.wait.until(EC.element_to_be_clickable(DHLTrackingLocators.CUSTOM_DROPOFF_INPUT))
        inp.clear()
        inp.send_keys(text)

    def click_consent_checkbox(self) -> None:
        checkbox = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']")))
        checkbox.click()

    def click_confirm(self) -> None:
        confirm = self.wait.until(EC.element_to_be_clickable(DHLTrackingLocators.CONFIRM_BUTTON))
        confirm.click()
