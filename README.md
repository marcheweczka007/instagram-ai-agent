# Instagram Brand Research Assistant

AI-assisted brand research for Instagram creator collaborations.

Discover relevant creators, scrape public profile signals, score them, evaluate **brand fit**, and export a manager-ready research pack (Markdown + CSV + JSON).

> Built as a portfolio-grade Python application with a clean layered architecture.

---

## Overview

This is **not** a generic “Instagram scorer”.

It answers:

> How good of a collaboration partner is this creator **for this specific brand**?

Typical flow:

1. Discover Instagram profile URLs for a topic  
2. Scrape public profile data (Browser Use)  
3. Score creator quality  
4. Research brand fit  
5. Export ranked report artifacts  

---

## Architecture

```text
┌──────────────────────────────┐
│ CLI / pipelines              │
│  discover_and_research()     │
│  analyse_profile(s)          │
└──────────────┬───────────────┘
               │
     ┌─────────┴─────────┐
     ▼                   ▼
┌────────────┐    ┌─────────────────┐
│ Agents     │    │ Browser         │
│ Discovery  │    │ InstagramScraper│
│ Scorer     │    └────────┬────────┘
│ Research   │             │
└─────┬──────┘             │
      │                    │
      └────────┬───────────┘
               ▼
      ┌────────────────┐
      │ Domain models  │
      └───────┬────────┘
              ▼
      ┌──────────────────────────┐
      │ Services                 │
      │ CSV / JSON / Markdown    │
      └──────────────────────────┘
```

---

## Folder structure

```text
instagram-agent/
├── data/
│   └── example_profile.json
├── outputs/
│   ├── csv/
│   ├── reports/
│   └── logs/
├── src/instagram_agent/
│   ├── agents/          # Discovery, Scorer, Research
│   ├── browser/         # Instagram scraper (Browser Use)
│   ├── domain/          # Pydantic models
│   ├── infrastructure/  # OpenAI client
│   ├── pipelines/       # Orchestration
│   ├── prompts/         # Agent prompts
│   ├── services/        # CSV / JSON / report formatters
│   ├── cli.py           # Interactive menu
│   └── config.py        # Settings
├── tests/
├── README.md
├── PROJECT_REVIEW.md
└── pyproject.toml
```

---

## Installation

Requirements:
- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key

```bash
git clone <your-repo-url>
cd instagram-agent
uv sync --extra dev
cp .env.example .env
```

Edit `.env` and set:

```bash
OPENAI_API_KEY=sk-...
```

---

## Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `OPENAI_API_KEY` | required | OpenAI auth |
| `OPENAI_MODEL` | `gpt-5` | Scoring / research model |
| `EXTRACTION_MODEL` | `gpt-5-mini` | Browser page extraction model |
| `BROWSER_MAX_STEPS` | `8` | Browser Use max steps |
| `BROWSER_TIMEOUT_SECONDS` | `60` | Scraper wall timeout |
| `DISCOVERY_TIMEOUT_SECONDS` | `90` | Discovery wall timeout |
| `DISCOVERY_MAX_RESULTS` | `20` | Max discovered URLs |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Usage

### Interactive CLI

```bash
uv run python -m instagram_agent
```

Menu:

1. Discover creators  
2. Analyse profile  
3. Brand research  
4. Export report  
5. Quit  

### Library API

```python
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.pipelines import discover_and_research

brand = build_jollyzu_brand()
results = await discover_and_research("upcycled bags", brand)
```

Artifacts are written to:

- `outputs/csv/`
- `outputs/reports/` (Markdown + JSON)
- `outputs/logs/`

---

## Example commands

```bash
# CLI
uv run python -m instagram_agent

# Unit tests
uv run pytest

# Lint
uvx ruff check src tests
uvx ruff format src tests
```

---

## Screenshots

> Placeholder — add CLI / report screenshots before publishing.

![CLI placeholder](docs/screenshots/cli.png)

![Report placeholder](docs/screenshots/report.png)

---

## Outputs

Each brand research run can produce:

| Artifact | Format | Purpose |
|----------|--------|---------|
| Ranked creators | CSV | Spreadsheet review |
| Brand research report | Markdown | Manager-readable narrative |
| Summary | JSON | API / automation handoff |

Results are sorted by `brand_fit` descending.

---

## Future roadmap

- FastAPI service layer for SaaS
- Multi-platform creator adapters (TikTok, YouTube, Pinterest)
- Persistent storage + brand workspaces
- Concurrent analysis with rate limiting
- Human-in-the-loop outreach drafting

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Project review

See [PROJECT_REVIEW.md](PROJECT_REVIEW.md) for architecture strengths, debt, and next steps.
