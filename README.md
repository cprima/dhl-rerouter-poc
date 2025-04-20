# dhl-rerouter-poc

Proof‑of‑concept for automated DHL delivery rerouting via IMAP and Selenium.

## Use Case  
Automate handling of incoming DHL shipments when you’re away: fetch tracking codes from your email, check your calendar for “away” events, and pre‑emptively set an alternate drop‑off location on DHL’s website.

## User Story  
> **As** a frequent online shopper who isn’t always at home,  
> **I want** a script that automatically reads my latest tracking codes, verifies if I’m away, and reroutes packages before delivery,  
> **so that** I never miss or lose a parcel and don’t have to manually log into DHL each time.

## Value Proposition  
- **Save Time:** Replaces manual inbox‑search, regex parsing, and browser clicks with a single command.  
- **Ensure Reliability:** Triggers reroute requests precisely when calendar events indicate you’ll be away.  
- **Maintain Flexibility:** Modular Python code that can evolve—adding carriers or migrating into n8n without rewriting.  
- **Offer Transparency:** “Highlight‑only” mode visually confirms each step before any real clicks.


## Workflow Diagram

```
      +--------------+
      |   START      |
      +--------------+
             |
             v
      +--------------+
      | Fetch emails |
      |   (IMAP)     |
      +--------------+
             |
             v
      +--------------+
      | Parse bodies |
      | extract codes|
      +--------------+
             |
             v
      +--------------+
      | Deduplicate  |
      |   codes      |
      +--------------+
             |
             v
      +--------------------------------+
      | For each code in codes:       |
      +--------------------------------+
             |
             v
      +------------------+
      | carrier == DHL?  |
      +------------------+
         |        |
        No       Yes
         |         v
         |   +---------------------+
         |   | check_availability  |
         |   | (reroute_checker)   |
         |   +---------------------+
         |         |
         |         v
         |   +---------------------+
         |   | get delivery_date & |
         |   | available options   |
         |   +---------------------+
         |         |
         |         v
         |   +---------------------+
         |   | calendar check      |
         |   | (should_reroute)    |
         |   +---------------------+
         |         |
         |    No   | Yes
         |         v
         |   +---------------------+
         |   | reroute_shipment    |
         |   | (reroute_executor)  |
         |   +---------------------+
         |         |
         v         v
   +-----------+  +-----------+
   |  SKIP     |  |   END     |
   +-----------+  +-----------+
```

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

## Usage

Run the main workflow:
```bash
uv run -- python -m dhl_rerouter_poc.main \
  --weeks 2 \
  --zip 12345 \
  --location "My Office"
```
or, after activating the venv:
```bash
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
# or `source .venv/bin/activate` on macOS/Linux
python -m dhl_rerouter_poc.main --weeks 2 --zip 12345 --location "My Office"
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