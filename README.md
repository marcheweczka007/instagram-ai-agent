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
| `GOOGLE_SHEETS_ENABLED` | `false` | Enable live Sheets export |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | `credentials.json` | Service account JSON path |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | empty | Target spreadsheet ID |
| `GOOGLE_SHEETS_WORKSHEET_NAME` | `Creators` | Worksheet / tab name |
| `NOTION_ENABLED` | `true` | Enable Notion Creator CRM |
| `NOTION_TOKEN` | empty | Notion internal integration token |
| `NOTION_DATABASE_ID` | empty | Target Notion database ID |

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
| Creator CRM rows | Notion | Primary collaborative workspace |
| Live spreadsheet rows | Google Sheets | Optional secondary live sink |
| Ranked creators | CSV | Offline backup / fallback |
| Brand research report | Markdown | Manager-readable narrative |
| Summary | JSON | API / automation handoff |

Results are sorted by `brand_fit` descending.

When Notion is configured, each creator is **upserted immediately** after research.
If Notion fails, the exporter falls back to CSV (`outputs/csv/notion_fallback.csv`) and the pipeline continues.

---

## Notion Creator CRM setup

Notion is the preferred live CRM workspace. Each researched creator is upserted immediately after analysis.

### 1. Create a Notion integration

1. Open [Notion My Integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Name it (for example `Instagram Brand Research`)
4. Choose the workspace that owns your CRM database
5. Set capabilities to include **Read content** and **Update content**

### 2. Obtain `NOTION_TOKEN`

1. Open the integration page
2. Copy the **Internal Integration Secret**
3. Put it in `.env` as `NOTION_TOKEN`

### 3. Obtain `NOTION_DATABASE_ID`

1. Create a Notion **database** (full-page database works best)
2. Open the database as a full page
3. Copy the ID from the URL:

```text
https://www.notion.so/workspace/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...
                               └──────────── DATABASE_ID ────────────┘
```

Use the 32-character ID (with or without dashes).

### 4. Connect the database to the integration

1. Open the database in Notion
2. Click **••• → Connections** (or **Add connections**)
3. Select your integration
4. Confirm access

Without this step, API calls will fail with permission errors.

### 5. Database schema (auto-created)

You only need an empty Notion database connected to the integration.

On `connect()`, the app calls `ensure_schema()` and automatically creates any missing properties:

| Property | Type | Notes |
|----------|------|------|
| Creator | Title | Renames the database's existing Title column if needed |
| Instagram URL | URL | Unique key used for upserts |
| Followers | Number | |
| Score | Number | |
| Brand Fit | Number | |
| Confidence | Number | |
| Priority | Select | Options: `High`, `Medium`, `Low` |
| Status | Status | Option `New` on create; falls back to Select if needed |
| Suggested Comment | Rich text | |
| Suggested DM | Rich text | |
| First Outreach Angle | Rich text | |
| Collaboration Ideas | Rich text | |
| Strengths | Rich text | |
| Weaknesses | Rich text | |
| AI Notes | Rich text | |
| Last Analysed | Date | |

Manual property setup is not required.

### 6. Enable in `.env`

```bash
NOTION_ENABLED=true
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 7. Test create + update (no duplicates)

```bash
uv run python -m instagram_agent.notion_test
```

Expected behaviour:
- first run creates the page with `Status=New`
- second run updates the same page (same Instagram URL)
- `Status` is not overwritten on update

If Notion is unavailable, rows fall back to `outputs/csv/notion_fallback.csv` and the pipeline continues.

---

## Google Sheets setup

Google Sheets is an optional secondary live sink when Notion is not configured. CSV remains the automatic fallback.

### 1. Create a Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)

### 2. Enable the Sheets API

1. Go to **APIs & Services → Library**
2. Enable **Google Sheets API**
3. Also enable **Google Drive API** (required for service-account spreadsheet access)

### 3. Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **Create credentials → Service account**
3. Name it (for example `instagram-agent-sheets`)
4. Skip optional permissions unless your org requires them

### 4. Download `credentials.json`

1. Open the service account
2. Go to **Keys → Add key → Create new key → JSON**
3. Save the file as `credentials.json` in the project root  
   (path configurable via `GOOGLE_SHEETS_CREDENTIALS_PATH`)
4. Never commit this file — it is gitignored

### 5. Share the spreadsheet with the Service Account email

1. Create a Google Sheet (or open an existing one)
2. Copy the spreadsheet ID from the URL:  
   `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`
3. Share the sheet with the service account email  
   (looks like `...@....iam.gserviceaccount.com`) as **Editor**
4. Put the ID in `.env`:

```bash
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_WORKSHEET_NAME=Creators
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
```

### 6. Test

```bash
uv run python -m instagram_agent.google_sheets_test
```

Expected columns:

`Creator | Instagram URL | Followers | Score | Brand Fit | Confidence | Suggested Comment | Suggested DM | Status | Notes`

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
