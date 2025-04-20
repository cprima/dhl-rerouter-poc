# selectors_dhlde.py
from selenium.webdriver.common.by import By

# Shipment status
DELIVERY_STATUS = "//strong[contains(text(),'shipment')]"
DELIVERY_DATE = "//*[contains(text(),'Estimated delivery')]/following-sibling::*"
DELIVERED_TEXTS = "//*[contains(text(),'delivered') or contains(text(),'zustellt')]"

# Delivery options toggle + items
DELIVERY_TOGGLE = "//section//button[contains(., 'You are not at home')]"
DELIVERY_OPTIONS = "//div[@class='verfuegen-container']//li[@data-name]"

# Shipment history entries
SHIPMENT_HISTORY_ENTRY = "li[data-testid='shipment-course-entry']"

# Freeform drop-off input
CUSTOM_DROPOFF_INPUT = "div.shipmentServices form div.radioFormgroup.otherDropPoint input[type='text']"


def delivery_status_selector(tracking_number):
    return (
        By.CSS_SELECTOR,
        f"section[data-testid='shipment-details'] article.shipment "
        f"div[data-shipment-id='{tracking_number}'] div[data-testid^='status-body_'] p > strong"
    )

ALLOWED_DELIVERY_OPTION_KEYS = {
    "PREFERRED_LOCATION",
    "PREFERRED_DAY",
    "MERGED_LR_PACKSTATION_AND_BRANCH",
    "PREFERRED_NEIGHBOUR",
    "DELIVERY_CANCELLATION",
    "COLLECT_ON_INSTRUCTION"
}
