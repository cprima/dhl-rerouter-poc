```markdown
# dhl-rerouter-poc

Proof‑of‑concept for automated DHL delivery rerouting via IMAP and Selenium.

## Prerequisites
- Python 3.13+
- [uv](https://astral.sh/uv) (installed globally via `pipx install uv`)

## Installation
```bash
git clone git@github.com:cprima/dhl-rerouter-poc.git
cd dhl-rerouter-poc
uv sync
```

## Configuration

1. Copy and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
2. Edit `config.yaml`:
   ```yaml
   email:
     host: imap.mailbox.org
     port: 993
     ssl: true
     folders:
       - INBOX
       - INBOX/pending
       - Einkauf
     lookback_weeks: 4
   tracking_patterns:
     DHL:
       - '\bJJD\d{10,}\b'
       - '\b0034\d{8,}\b'
     # …
   ```

## Usage

Run the main workflow:
```bash
uv run -- python -m dhl_rerouter_poc.main \
  --weeks 2 \
  --zip 38448 \
  --location "My Office"
```
or, after activating the venv:
```bash
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
# or `source .venv/bin/activate` on macOS/Linux
python -m dhl_rerouter_poc.main --weeks 2 --zip 38448 --location "My Office"
```

## Project Layout
```
dhl-rerouter-poc/
├── .env.example
├── config.yaml
├── pyproject.toml
├── dhl_rerouter_poc/
│   ├── __init__.py
│   ├── config.py
│   ├── email_client.py
│   ├── parser.py
│   ├── calendar_checker.py
│   ├── reroute_checker.py
│   ├── reroute_executor.py
│   ├── selectors_dhlde.py
│   └── main.py
├── LICENSE        # CC‑BY
└── AUTHORS.md
```

## License  
CC‑BY 4.0  
```