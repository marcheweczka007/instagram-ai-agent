"""Application settings and environment loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Central configuration for the Instagram Brand Research Assistant."""

    openai_api_key: str
    openai_model: str = "gpt-5"
    extraction_model: str = "gpt-5-mini"

    browser_max_steps: int = 8
    browser_timeout_seconds: float = 60.0
    discovery_timeout_seconds: float = 90.0
    discovery_max_results: int = 20
    llm_http_timeout_seconds: float = 40.0
    extraction_http_timeout_seconds: float = 30.0
    llm_call_timeout_seconds: float = 40.0
    step_timeout_seconds: float = 50.0

    log_level: str = "INFO"

    output_dir: Path = Path("outputs")
    csv_dir: Path = Path("outputs/csv")
    reports_dir: Path = Path("outputs/reports")
    logs_dir: Path = Path("outputs/logs")

    recommend_brand_fit_min: int = 8
    avoid_brand_fit_max: int = 4

    google_sheets_credentials_path: Path = Path("credentials.json")
    google_sheets_spreadsheet_id: str = ""
    google_sheets_worksheet_name: str = "Creators"
    google_sheets_enabled: bool = False

    def ensure_output_dirs(self) -> None:
        """Create standard output folders if missing."""
        for path in (self.output_dir, self.csv_dir, self.reports_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in .env")

    return Settings(
        openai_api_key=api_key,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5"),
        extraction_model=os.getenv("EXTRACTION_MODEL", "gpt-5-mini"),
        browser_max_steps=int(os.getenv("BROWSER_MAX_STEPS", "8")),
        browser_timeout_seconds=float(os.getenv("BROWSER_TIMEOUT_SECONDS", "60")),
        discovery_timeout_seconds=float(os.getenv("DISCOVERY_TIMEOUT_SECONDS", "90")),
        discovery_max_results=int(os.getenv("DISCOVERY_MAX_RESULTS", "20")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        google_sheets_credentials_path=Path(
            os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials.json")
        ),
        google_sheets_spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip(),
        google_sheets_worksheet_name=os.getenv(
            "GOOGLE_SHEETS_WORKSHEET_NAME", "Creators"
        ).strip()
        or "Creators",
        google_sheets_enabled=os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower()
        in {"1", "true", "yes", "on"},
    )


# Backward-compatible module attribute used by existing imports.
def __getattr__(name: str) -> str:
    if name == "OPENAI_API_KEY":
        return get_settings().openai_api_key
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
