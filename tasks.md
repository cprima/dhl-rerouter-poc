# Streamlining Arguments and Parameterization Tasks

# Streamlining Arguments and Parameterization Tasks

## 3. Use a Typed Config Object
- Refactor config access to use TypedDict or dataclass for config sections (e.g., `DHLConfig`, `EmailConfig`).
- Improves type safety, autocompletion, and maintainability.

## 4. CLI Help and Defaults
- Dynamically set argparse defaults from config so `--help` shows actual defaults.
- Load config before parser definition to enable this.

---

## Backlog
- Optionally add the `timeout` key (with comment) to `config.yaml.example` for documentation clarity, since it is now a configurable runtime parameter but defaults to 20 if omitted.

If you want to implement any of these, let Cascade know for a step-by-step refactor proposal or code changes!
