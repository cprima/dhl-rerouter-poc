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

> **Important:** Email credentials (user and password) are never stored in config files. Instead, set them via environment variables `MAILBOX_USER` and `MAILBOX_PASS`, typically in a `.env` file at the project root. See `.env.example` for the required format.

### Test Configuration

To run tests, you need a test configuration file:

1. Copy `config_test.yaml.example` to `config_test.yaml`.
2. Fill in the required values for your test environment (safe test credentials only). **Do not add your email username or password here.**
3. Set your email credentials in a `.env` file using `MAILBOX_USER` and `MAILBOX_PASS`.
4. `config_test.yaml` is gitignored and should never be committed.
5. Tests will load `config_test.yaml` for their configuration, and always read credentials from the environment.


1. Copy and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
2. Edit `config.yaml`:

## Usage

You can run the main workflow with all arguments, or rely on config.yaml for defaults. CLI arguments always take precedence over config.yaml values.

### With explicit CLI arguments (overrides config):
```bash
uv run -- python -m dhl_rerouter_poc.main \
  --weeks 2 \
  --zip 12345 \
  --location "My Office" \
  --highlight-only \
  --selenium-headless \
  --timeout 30
```

### Using config.yaml values (omit any or all arguments):
```bash
uv run -- python -m dhl_rerouter_poc.main
```

You can also override just one or two arguments:
```bash
uv run -- python -m dhl_rerouter_poc.main --zip 38448 --highlight-only
```

**Parameter Precedence:**
- If a CLI argument is provided, it overrides the value in config.yaml.
- If a CLI argument is omitted, the value from config.yaml is used.
- If neither is provided, the script will raise an error for required parameters.

**Configurable Parameters:**
| CLI Argument         | Config Key                        | Description                                             | Default (if any)         |
|---------------------|-----------------------------------|---------------------------------------------------------|--------------------------|
| `--weeks`           | `email.lookback_weeks`            | Lookback period in weeks for email search               | Required                 |
| `--zip`             | `dhl.zip`                         | Postal code for DHL tracking page                       | Required                 |
| `--location`        | `dhl.reroute_location`            | Custom drop‑off location text                           | Required                 |
| `--highlight-only`  | `dhl.highlight_only`              | Only highlight the confirm button, do not click         | `True`                   |
| `--selenium-headless`| `dhl.selenium_headless`           | Run Selenium browser in headless mode                   | `False`                  |
| `--timeout`         | `dhl.timeout`                     | Timeout for Selenium waits (seconds)                    | `20`                     |

Or, after activating the venv:
```bash
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
# or `source .venv/bin/activate` on macOS/Linux
python -m dhl_rerouter_poc.main
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