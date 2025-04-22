"""
Locators for DHL tracking page elements.
"""
from selenium.webdriver.common.by import By

class DHLTrackingLocators:
    @staticmethod
    def shipment_content_div(tracking_number: str):
        """
        Returns a locator tuple for the shipment content div for a given tracking number,
        where the div is a direct child of an article with class 'shipment'.
        Usage: wait.until(EC.visibility_of_element_located(DHLTrackingLocators.shipment_content_div(tracking_number)))
        """
        return (
            By.CSS_SELECTOR,
            f'article.shipment > div[data-shipment-id="{tracking_number}"]'
        )
    # DELIVERY_STATUS: <strong> inside the shipment article, content should be 'Delivery successful.'
    DELIVERY_STATUS = (By.CSS_SELECTOR, "article.shipment strong")
    DELIVERY_DATE = (By.XPATH, "//article[contains(@class, 'shipment')]/div[@data-shipment-id]/div[2]//time")
    DELIVERED_TEXTS = (By.XPATH, "//*[contains(text(),'delivered') or contains(text(),'zustellt')]")
    DELIVERY_TOGGLE = (By.XPATH, "//section//button[contains(., 'You are not at home')]")
    DELIVERY_OPTIONS = (By.XPATH, "//div[@class='verfuegen-container']//li[@data-name]")
    SHIPMENT_HISTORY_ENTRY = (By.CSS_SELECTOR, "li[data-testid='shipment-course-entry']")
    CUSTOM_DROPOFF_INPUT = (By.CSS_SELECTOR, "div.shipmentServices form div.radioFormgroup.otherDropPoint input[type='text']")
    CONFIRM_BUTTON = (By.XPATH, "//button[text()='Confirm']")
    # DELIVERED_TO: <p> following a <p> with text 'Delivered to:'
    DELIVERED_TO = (By.XPATH, "//p[normalize-space(text())='Delivered to:']/following-sibling::p[1]")
    # DELIVERED_TO_FALLBACK: last <p> in the delivery info div (fallback if label changes)
    DELIVERED_TO_FALLBACK = (
        By.XPATH,
        "//article[contains(@class, 'shipment')]/div[@data-shipment-id]/div[2]/descendant::p[last()]"
    )

    @classmethod
    def get_delivered_to(cls, driver: 'selenium.webdriver.remote.webdriver.WebDriver', logger: 'logging.Logger', delivered: bool) -> 'selenium.webdriver.remote.webelement.WebElement | None':
        """
        Attempts to locate the recipient element if delivered is True.
        If delivered is False or None, does not attempt any delivered_to selector and returns None.
        Logs which selector was used. Returns the WebElement or None if not found.
        """
        if not delivered:
            logger.info("Delivered status is False or None, not attempting to find recipient.")
            return None
        from selenium.common.exceptions import NoSuchElementException
        try:
            el = driver.find_element(*cls.DELIVERED_TO)
            logger.info("Recipient found using DELIVERED_TO selector.")
            return el
        except NoSuchElementException:
            logger.info("Primary DELIVERED_TO selector failed, trying fallback.")
            try:
                el = driver.find_element(*cls.DELIVERED_TO_FALLBACK)
                logger.info("Recipient found using DELIVERED_TO_FALLBACK selector.")
                return el
            except NoSuchElementException:
                logger.error("Could not find recipient element using either selector.")
                return None
