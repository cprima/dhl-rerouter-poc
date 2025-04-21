# Solution Design (Current Status)

## 1. Overview
Proof‑of‑concept Python package (`dhl-rerouter-poc`) to:
- Fetch recent emails via IMAP
- Extract parcel tracking codes (DHL & other carriers)
- Check calendar rules (stubbed)
- Scrape DHL website for reroute options
- Execute reroute via Selenium (stubbed)

## 2. Project Layout
```
dhl-rerouter-poc/
├── .env.example            # credentials template
├── config.yaml             # IMAP, folders, lookback, regex patterns
├── pyproject.toml          # project & dependencies (uv/PEP621)
├── dhl_rerouter_poc/
│   ├── __init__.py         # disables undetected‑chromedriver __del__
│   ├── config.py           # loads config.yaml + .env
│   ├── email_client.py     # IMAP client, messages sorted newest→oldest
│   ├── parser.py           # regex extractor, HTML stripper
│   ├── calendar_checker.py # stub: should_reroute(code) → bool
│   ├── reroute_checker.py  # DHL scrape → availability dict
│   ├── reroute_executor.py # stub: reroute_shipment(...) → bool
│   ├── selectors_dhlde.py  # all Selenium locators (unchanged)
│   └── main.py             # orchestrates workflow & CLI
├── LICENSE                 # CC‑BY 4.0
└── AUTHORS.md
```

## 3. Configuration
- **`.env`** (private):
  ```dotenv
  MAILBOX_USER=you@example.com
  MAILBOX_PASS=supersecret
  ```
- **`config.yaml`**:
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
    Hermes:
      - '\bHR\d{10}\b'
    UPS:
      - '\b1Z[0-9A-Z]{16}\b'
    DPD:
      - '\b0145\d{8}\b'
    eBay Global:
      - '\bEE\d{25}N\b'
    GLS:
      - '\b\d{11}\b'
  ```

## 4. Workflow
1. **Fetch & sort** emails from each folder (newest first via IMAP SORT or reversed SEARCH).  
2. **Parse** each message body for tracking codes.  
3. **Deduplicate** codes across all messages.  
4. **Filter** by carrier (currently only DHL).  
5. **Calendar check** (stub: always reroute).  
6. **Availability scrape** (`reroute_checker.check_reroute_availability`) returns options.  
7. **Execute reroute** (`reroute_executor.reroute_shipment`, currently stub).

## 5. Usage
```bash
uv run -- python -m dhl_rerouter_poc.main \
  --weeks 2 \
  --zip 12345 \
  --location "My Office"
```
Or, after activating `.venv`:
```bash
python -m dhl_rerouter_poc.main --weeks 2 --zip 12345 --location "My Office"
```

## 6. Next Steps
- Implement `calendar_checker.should_reroute` logic
- Flesh out `reroute_executor` with Selenium actions
- Add logging & error handling
- Write unit tests & CI pipeline
- Prepare for n8n migration by mapping each function to workflow nodes
