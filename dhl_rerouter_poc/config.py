import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

def load_config():
    cfg = yaml.safe_load(Path(Path(__file__).parent.parent / "config.yaml").read_text())
    # inject creds
    user = os.getenv("MAILBOX_USER")
    pwd  = os.getenv("MAILBOX_PASS")
    if not user or not pwd:
        raise RuntimeError("Set MAILBOX_USER and MAILBOX_PASS in .env")
    cfg["email"]["user"]     = user
    cfg["email"]["password"] = pwd
    return cfg
