import re
import logging
logger = logging.getLogger(__name__)

def extract_tracking_codes(text: str, patterns: dict, run_id: str | None = None) -> dict:
    if run_id:
        logger.info("Going to extract tracking codes [run_id=%s]", run_id)
    else:
        logger.info("Going to extract tracking codes")
    found = {}
    for carrier, pats in patterns.items():
        for pat in pats:
            for m in re.findall(pat, text):
                found[m] = carrier
    if run_id:
        logger.debug("Finished extracting tracking codes [run_id=%s]", run_id)
    else:
        logger.debug("Finished extracting tracking codes")
    return found

def safe_decode(payload, charset):
    try:
        return payload.decode(charset, errors="ignore")
    except:
        return payload.decode("utf-8", errors="ignore")

def strip_html(html):
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "html.parser").get_text()
