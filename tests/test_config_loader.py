import os
import shutil
import tempfile
from pathlib import Path
import pytest
import yaml

from dhl_rerouter_poc import config as config_mod

@pytest.fixture
def temp_project_config():
    """
    Copies config.yaml.example to project root as config.yaml, backs up any existing config.yaml.
    Cleans up after test.
    """
    project_root = Path(__file__).parent.parent
    example_path = project_root / "config.yaml.example"
    config_path = project_root / "config.yaml"
    backup_path = None
    if config_path.exists():
        backup_path = project_root / "config.yaml.bak"
        shutil.move(str(config_path), str(backup_path))
    shutil.copy(str(example_path), str(config_path))
    yield config_path
    config_path.unlink()
    if backup_path and backup_path.exists():
        shutil.move(str(backup_path), str(config_path))

@pytest.mark.parametrize(
    "env_vars,expected_mailboxes", [
        (
            {
                "MAILBOX_USER": "user1@example.com",
                "MAILBOX_PASS": "pass1",
                "HOTMAIL_MAILBOX_USER": "user2@example.com",
            },
            ["personal", "hotmail-graph"],
        ),
    ],
)
def test_load_config_injects_env(monkeypatch, temp_project_config, env_vars, expected_mailboxes):
    # Set environment variables
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    cfg = config_mod.load_config()
    mailbox_names = [mbox["name"] for mbox in cfg["mailboxes"]]
    assert mailbox_names == expected_mailboxes
    # Check credentials injected
    for mbox in cfg["mailboxes"]:
        access = mbox["access"]
        if access["type"] == "imap":
            assert mbox["user"] == env_vars[access["user_env"]]
            assert mbox["password"] == env_vars[access["pass_env"]]
        elif access["type"] == "ms_graph":
            assert mbox["user"] == env_vars[access["user_env"]]
