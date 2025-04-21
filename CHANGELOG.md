# Changelog

## [v0.3.0] - Unreleased
### Major Features & Improvements
- **Workflow-wide run_id traceability:** All major workflow steps and log entries now include a unique `run_id`, enabling end-to-end traceability and cross-module log correlation for every shipment rerouting automation run.
- **Logging refactor:** All modules now use module-level loggers (`logger = logging.getLogger(__name__)`), ensuring consistent, filterable, and maintainable log output. Structured "Going to..." and "Finished..." messages are present at key workflow steps, always including the `run_id` where available.
- **Unified configuration:** Centralized configuration loading, typed config, and dynamic CLI help defaults. CLI/config precedence is now consistent and runtime options are improved.
- **Model-driven workflow:** The workflow is now orchestrated using a unified, Pydantic-based data model (`ShipmentLifecycle`), improving type safety, validation, and extensibility.
- **Testing & documentation:** Added parametrized workflow tests and improved documentation for config and workflow data model.

### Bug Fixes & Refactoring
- Fixed logging inconsistencies and removed hardcoded logger names.
- Improved Selenium and configuration handling for better test/prod consistency.
- Ensured all modules follow Python logging best practices.

---

## [v0.2.0-alpha] - 2025-04-21
### Major Features & Refactorings
- **Unified Workflow Data Model:** Introduced a Pydantic-based model (`ShipmentLifecycle` and related classes) to represent the entire shipment lifecycle, enabling type safety, validation, and future extensibility (multi-carrier, richer state).
- **Model-Driven Workflow:** Refactored main orchestration (`main.py`) to use the new data model at every stage, replacing ad hoc data passing with structured, validated context objects.
- **Comprehensive Testing:** Added a robust pytest suite for the workflow data model, covering unit, integration, and edge cases.
- **Environment-Driven Model Debug Logging:** Implemented a logging utility to output model state at key workflow stages, opt-in via the `DEBUG_MODEL` environment variable, logging at INFO level for clarity.
- **Repo-Wide Warning Suppression:** Suppressed noisy DeprecationWarnings from third-party dependencies for cleaner test and runtime logs.
- **Documentation:** Added project report and model documentation under `docs/`, clarified `.env.example` usage.

### Improvements
- Enhanced configuration management and security by ensuring all credentials are handled via environment variables and YAML config.
- Improved code organization by separating logging utilities and model logic from workflow orchestration.
- Updated backlog and project documentation to reflect new architecture and future-proofing recommendations.

---

## [v0.1.0] - Initial Release
### Initial Technical Implementation
- Implemented DHL rerouting automation: IMAP email monitoring, tracking code extraction, calendar-based reroute decision, Selenium-based reroute execution.
- Modular design: email client, parser, calendar checker, reroute checker/executor.
- Configuration via YAML and environment variables.
- Basic unit tests for core modules.

---

*For a complete list of commits and changes, see the project’s git history and tags.*
