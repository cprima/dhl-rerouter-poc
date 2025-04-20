# dhl_rerouter_poc/utils.py

from datetime import datetime

def parse_dhl_date(date_str: str) -> str | None:
    """
    Parses strings like 'Tu, 22.04.2025' into ISO date '2025-04-22'.
    Returns None on parse or weekday mismatch.
    """
    weekday_map = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
    try:
        weekday_part, date_part = [s.strip() for s in date_str.split(",", 1)]
        expected = weekday_map.get(weekday_part)
        parsed = datetime.strptime(date_part, "%d.%m.%Y").date()
        if expected is None or parsed.weekday() != expected:
            return None
        return parsed.isoformat()
    except Exception:
        return None

# dhl_rerouter_poc/utils.py

import time
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

def blink_element(
    driver: WebDriver,
    element: WebElement,
    times: int = 5,
    color: str = "green",
    width: int = 10,
    interval: float = 0.3
) -> None:
    """
    Blink the given element by repeatedly applying and removing
    a colored border.

    :param driver:   Selenium WebDriver instance
    :param element:  WebElement to highlight
    :param times:    Number of blink cycles
    :param color:    Border color
    :param width:    Border width in pixels
    :param interval: Seconds between on/off
    """
    # capture original style
    orig = driver.execute_script("return arguments[0].style.border", element) or ""
    blink_style = f"{width}px solid {color}"

    for _ in range(times):
        driver.execute_script(f"arguments[0].style.border='{blink_style}'", element)
        time.sleep(interval)
        driver.execute_script(f"arguments[0].style.border='{orig}'", element)
        time.sleep(interval)
