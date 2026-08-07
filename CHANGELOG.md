# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-08-07

### Added
- Central `Settings` configuration via environment variables
- Standard pipeline logging (`START` / `SUCCESS` / `FAILURE` + timing)
- `outputs/csv`, `outputs/reports`, `outputs/logs` layout
- JSON summary exporter
- Interactive CLI (`python -m instagram_agent`)
- Implemented `discover_and_research()` end-to-end pipeline
- Pytest suite for core domain logic and formatters
- README, LICENSE, CONTRIBUTING, CHANGELOG, PROJECT_REVIEW

### Changed
- Shared OpenAI client factory (`create_client`)
- Browser Use LLM construction centralized in `browser/llm.py`
- Scorer / Research / Discovery / Scraper read model and timeout settings from config
- Example profile JSON aligned with `InstagramProfile`

### Fixed
- Root-level export paths redirected to `outputs/`
- Scorer now raises when structured parse returns `None`
