# dhl_rerouter_poc/email_client.py

import imaplib
import email
from datetime import datetime, timedelta
from .parser import safe_decode, strip_html

import logging
logger = logging.getLogger(__name__)

class ImapEmailClient:
    def __init__(self, cfg: dict):
        self.host     = cfg["host"]
        self.port     = cfg["port"]
        self.ssl      = cfg.get("ssl", True)
        self.user     = cfg["user"]
        self.pwd      = cfg["password"]
        self.folders  = cfg["folders"]
        self.lookback = cfg["lookback_weeks"]

    def fetch_messages(self, run_id: str | None = None):
        if run_id:
            logger.info("Going to fetch messages [run_id=%s]", run_id)
        else:
            logger.info("Going to fetch messages")
        mail = imaplib.IMAP4_SSL(self.host, self.port) if self.ssl else imaplib.IMAP4(self.host, self.port)
        mail.login(self.user, self.pwd)
        cutoff = (datetime.now() - timedelta(weeks=self.lookback)).strftime("%d-%b-%Y")
        msgs = []

        for folder in self.folders:
            status, _ = mail.select(f'"{folder}"', readonly=True)
            if status != "OK":
                continue

            # try server‐side SORT newest first
            try:
                status, data = mail.sort('REVERSE DATE', 'UTF-8', f'SINCE {cutoff}')
                nums = data[0].split() if status == "OK" else []
            except imaplib.IMAP4.error:
                # fallback to SEARCH + reverse
                status, data = mail.search(None, f'SINCE {cutoff}')
                nums = data[0].split()[::-1] if status == "OK" else []

            for num in nums:
                _, fetched = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(fetched[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        if ctype in ("text/plain", "text/html"):
                            ch = part.get_content_charset() or "utf-8"
                            txt = safe_decode(part.get_payload(decode=True), ch)
                            body += strip_html(txt) if ctype == "text/html" else txt
                else:
                    ch = msg.get_content_charset() or "utf-8"
                    body = safe_decode(msg.get_payload(decode=True), ch)
                msgs.append(body)

        mail.logout()
        if run_id:
            logger.debug("Finished fetching messages [run_id=%s]", run_id)
        else:
            logger.debug("Finished fetching messages")
        return msgs
