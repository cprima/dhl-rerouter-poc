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


def load_config() -> dict:
    """
    Load and process the main YAML configuration file, injecting mailbox credentials
    from environment variables as specified in each mailbox's access section.
    Returns the full config dict with credentials included and carrier configs merged.
    """
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise RuntimeError("config.yaml not found; copy config.yaml.example → config.yaml and fill in values")

    text = config_path.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text)

    mailboxes = cfg.get("mailboxes", [])
    for mbox in mailboxes:
        access = mbox.get("access", {})
        user_env = access.get("user_env")
        pass_env = access.get("pass_env")
        # For ms_graph, only user_env is expected
        if user_env:
            user_val = os.getenv(user_env)
            if not user_val:
                raise RuntimeError(f"Missing environment variable: {user_env} for mailbox '{mbox.get('name','?')}'")
            mbox["user"] = user_val
        if pass_env:
            pass_val = os.getenv(pass_env)
            if not pass_val:
                raise RuntimeError(f"Missing environment variable: {pass_env} for mailbox '{mbox.get('name','?')}'")
            mbox["password"] = pass_val
    cfg["mailboxes"] = mailboxes

    # Attach merged carrier configs for each carrier
    carriers = cfg.get("carriers", {})
    base_cfg = carriers.get("base", {})
    cfg["carrier_configs"] = {}
    for name, spec_cfg in carriers.items():
        if name == "base":
            continue
        cfg["carrier_configs"][name] = merge_carrier_config(base_cfg, spec_cfg)
    return cfg

