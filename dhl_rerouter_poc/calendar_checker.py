# dhl_rerouter_poc/calendar_checker.py

import logging
from datetime import datetime, timedelta

from caldav import DAVClient
from caldav.objects import Calendar


import logging
logger = logging.getLogger(__name__)

def should_reroute(tracking_number: str, delivery_date: str, config: dict, run_id: str | None = None) -> bool:
    """
    Return True if we should reroute this shipment,
    based on whether the user is 'away' on the given delivery_date.
    """

    if run_id:
        logger.info("Going to check calendar for reroute: tracking_number=%s, delivery_date=%s [run_id=%s]", tracking_number, delivery_date, run_id)
    else:
        logger.info("Going to check calendar for reroute: tracking_number=%s, delivery_date=%s", tracking_number, delivery_date)
    cal_cfg = config.get("calendar", {})
    if not cal_cfg.get("enabled", False):
        return True

    url       = cal_cfg["url"]             # full CalDAV collection URL
    lookahead = cal_cfg.get("lookahead_days", 1)
    user      = config["email"]["user"]
    pwd       = config["email"]["password"]

    # parse the delivery_date ISO string
    try:
        tgt_date = datetime.fromisoformat(delivery_date).date()
    except Exception as e:
        logger.error("Invalid delivery_date '%s': %s", delivery_date, e)
        return False

    start = tgt_date
    end   = tgt_date + timedelta(days=lookahead)

    try:
        client   = DAVClient(url, username=user, password=pwd)
        calendar = Calendar(client=client, url=url)

        # use date_search as in exploratory code
        events = calendar.date_search(start, end)

        for ev in events:
            title = getattr(ev.vobject_instance.vevent.summary, "value", "")
            if "away" in title.lower():
                logger.info("Found 'away' event '%s' on %s → reroute enabled", title, delivery_date)
                return True

        logger.info("No 'away' events on %s → skip reroute", delivery_date)
        return False

    except Exception as e:
        logger.error("Calendar check failed for %s: %s", delivery_date, e)
        # on any error, do not reroute
        return False
