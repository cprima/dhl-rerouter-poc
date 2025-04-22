"""
Factory for Selenium WebDriver setup.
"""
# Uses undetected-chromedriver to avoid Selenium detection on DHL and similar sites
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from typing import Optional

def create_chrome_driver(headless: bool = True, lang: str = "en", incognito: bool = True) -> uc.Chrome:
    """
    Create an undetected Chrome WebDriver with enhanced stealth settings for DHL anti-bot evasion.
    """
    options = Options()
    # Stealth: mimic real user environment
    if headless:
        options.add_argument("--headless=new")  # modern headless mode
    if lang:
        options.add_argument(f"--lang={lang}")
    if incognito:
        options.add_argument("--incognito")
    options.add_argument("--window-size=1200,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Realistic user-agent (update as needed)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    return uc.Chrome(options=options)
