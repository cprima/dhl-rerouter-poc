# Changelog

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
