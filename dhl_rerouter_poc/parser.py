import re
from .config import load_config

def extract_tracking_codes(text):
    patterns = load_config()["tracking_patterns"]
    found = {}
    for carrier, pats in patterns.items():
        for pat in pats:
            for m in re.findall(pat, text):
                found[m] = carrier
    return found

def safe_decode(payload, charset):
    try:
        return payload.decode(charset, errors="ignore")
    except:
        return payload.decode("utf-8", errors="ignore")

def strip_html(html):
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "html.parser").get_text()
