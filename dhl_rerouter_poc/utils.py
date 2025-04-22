# dhl_rerouter_poc/utils.py

from datetime import datetime, timedelta

def get_cutoff_since_date(days: int) -> str:
    """
    Returns a cutoff date string (e.g. '21-Apr-2025') for IMAP/Graph queries,
    given a lookback in days. 'days' means since midnight at the start of N days ago.
    Example: if now is 2025-04-22T11:00 and days=1, cutoff is 2025-04-21 00:00.
    Format: '%d-%b-%Y'.
    """
    now = datetime.now()
    cutoff = (now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days))
    return cutoff.strftime("%d-%b-%Y")

from typing import Optional
from datetime import datetime
import re
import importlib

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore


def parse_dhl_date(date_str: str) -> Optional[str]:
    """
    Parses DHL date strings like 'Tu, 22.04.2025, 12:23 hours' or 'Tu, 22.04.2025'.
    Returns ISO 8601 string (e.g., '2025-04-22T12:23:00+02:00' or '2025-04-22'), or None on parse/weekday mismatch.
    Timezone is loaded from config (carriers.DHL.timezone), defaults to 'Europe/Berlin'.
    """
    weekday_map = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
    try:
        # Lazy import to avoid circulars
        config_mod = importlib.import_module("dhl_rerouter_poc.config")
        cfg = config_mod.load_config()
        tz_name = (
            cfg.get("carrier_configs", {})
              .get("DHL", {})
              .get("timezone", "Europe/Berlin")
        )
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Berlin")

    try:
        parts = [s.strip() for s in date_str.split(",")]
        if len(parts) < 2:
            return None
        weekday_part, date_part = parts[:2]
        expected = weekday_map.get(weekday_part)
        parsed_date = datetime.strptime(date_part, "%d.%m.%Y").date()
        if expected is None or parsed_date.weekday() != expected:
            return None
        if len(parts) >= 3:
            match = re.match(r"(\d{1,2}):(\d{2})", parts[2])
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                dt = datetime.combine(parsed_date, datetime.min.time()).replace(hour=hour, minute=minute)
                dt = dt.replace(tzinfo=tz)
                return dt.isoformat(timespec="seconds")
        # If no time, return date only (no tz)
        return parsed_date.isoformat()
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
