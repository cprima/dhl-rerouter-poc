# dhl_rerouter_poc/config.py

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

def merge_carrier_config(base: dict, specific: dict) -> dict:
    """
    Merge base carrier config with carrier-specific overrides.
    Carrier-specific keys take precedence.
    """
    merged = dict(base or {})
    merged.update(specific or {})
    return merged


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise RuntimeError("config.yaml not found; copy config.yaml.example → config.yaml and fill in values")

    # read with explicit UTF‑8 encoding
    text = config_path.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text)

    user = os.getenv("MAILBOX_USER")
    pwd  = os.getenv("MAILBOX_PASS")
    if not user or not pwd:
        raise RuntimeError("Set MAILBOX_USER and MAILBOX_PASS in .env")

    cfg["email"]["user"]     = user
    cfg["email"]["password"] = pwd

    # Attach merged carrier configs for each carrier
    carriers = cfg.get("carriers", {})
    base_cfg = carriers.get("base", {})
    cfg["carrier_configs"] = {}
    for name, spec_cfg in carriers.items():
        if name == "base":
            continue
        cfg["carrier_configs"][name] = merge_carrier_config(base_cfg, spec_cfg)
    return cfg
