"""Export creator research rows to Google Sheets (CSV fallback)."""

from __future__ import annotations

import csv
import logging
from collections.abc import Sequence
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from instagram_agent.config import Settings, get_settings
from instagram_agent.domain.models import AnalysisResult, BrandResearchResult
from instagram_agent.logging_utils import default_csv_path

logger = logging.getLogger(__name__)

SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)

HEADERS: tuple[str, ...] = (
    "Creator",
    "Instagram URL",
    "Followers",
    "Score",
    "Brand Fit",
    "Confidence",
    "Suggested Comment",
    "Suggested DM",
    "Status",
    "Notes",
)

ExportRow = AnalysisResult | BrandResearchResult


class GoogleSheetsExporter:
    """Append brand-research rows to Google Sheets with CSV fallback."""

    def __init__(
        self,
        *,
        spreadsheet_id: str | None = None,
        worksheet_name: str | None = None,
        credentials_path: str | Path | None = None,
        fallback_csv_path: str | Path | None = None,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self._spreadsheet_id = (
            spreadsheet_id or cfg.google_sheets_spreadsheet_id or ""
        ).strip()
        self._worksheet_name = (
            worksheet_name or cfg.google_sheets_worksheet_name
        ).strip()
        self._credentials_path = Path(
            credentials_path or cfg.google_sheets_credentials_path
        )
        self._fallback_csv_path = Path(
            fallback_csv_path or default_csv_path("google_sheets_fallback")
        )
        self._client: gspread.Client | None = None
        self._spreadsheet: gspread.Spreadsheet | None = None
        self._worksheet: gspread.Worksheet | None = None
        self._using_csv_fallback = False

    def connect(self) -> None:
        """Authenticate with a Google service account and open the spreadsheet."""
        if not self._spreadsheet_id:
            raise ValueError(
                "Google Sheets spreadsheet ID is not configured. "
                "Set GOOGLE_SHEETS_SPREADSHEET_ID in .env."
            )
        if not self._credentials_path.exists():
            raise FileNotFoundError(
                f"Google service account credentials not found: {self._credentials_path}"
            )

        credentials = Credentials.from_service_account_file(
            str(self._credentials_path),
            scopes=SCOPES,
        )
        self._client = gspread.authorize(credentials)
        self._spreadsheet = self._client.open_by_key(self._spreadsheet_id)
        logger.info(
            "Connected to Google Sheet %s (worksheet=%s)",
            self._spreadsheet_id,
            self._worksheet_name,
        )

    def create_sheet_if_missing(self) -> None:
        """Ensure the target worksheet exists and has header row."""
        spreadsheet = self._require_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet(self._worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=self._worksheet_name,
                rows=1000,
                cols=len(HEADERS),
            )
            logger.info("Created worksheet %r", self._worksheet_name)

        self._worksheet = worksheet
        self._ensure_headers(worksheet)

    def append_result(self, result: ExportRow) -> None:
        """Append one analysed creator immediately (CSV fallback on failure)."""
        row = self._to_row(result)
        try:
            if self._using_csv_fallback:
                self._append_csv_row(row)
                return

            if self._worksheet is None:
                self.connect()
                self.create_sheet_if_missing()

            worksheet = self._require_worksheet()
            worksheet.append_row(row, value_input_option="USER_ENTERED")
            logger.info("Appended %s to Google Sheets", result.profile.name)
        except Exception:
            logger.exception(
                "Google Sheets append failed for %s; falling back to CSV",
                result.profile.name,
            )
            self._using_csv_fallback = True
            self._append_csv_row(row)

    def append_many(self, results: Sequence[ExportRow]) -> None:
        """Append many rows, writing each one immediately."""
        for result in results:
            self.append_result(result)

    def clear_sheet(self) -> None:
        """Clear worksheet values and rewrite headers."""
        try:
            if self._worksheet is None:
                self.connect()
                self.create_sheet_if_missing()
            worksheet = self._require_worksheet()
            worksheet.clear()
            worksheet.append_row(list(HEADERS), value_input_option="USER_ENTERED")
            logger.info(
                "Cleared worksheet %r and restored headers", self._worksheet_name
            )
        except Exception:
            logger.exception("Google Sheets clear failed; falling back to empty CSV")
            self._using_csv_fallback = True
            self._write_csv_headers()

    def _ensure_headers(self, worksheet: gspread.Worksheet) -> None:
        values = worksheet.row_values(1)
        if values[: len(HEADERS)] == list(HEADERS):
            return
        if not values:
            worksheet.append_row(list(HEADERS), value_input_option="USER_ENTERED")
            logger.info("Wrote Google Sheets headers")
            return
        # Header mismatch: insert headers at top without wiping existing data.
        worksheet.insert_row(list(HEADERS), index=1)
        logger.warning(
            "Existing header row did not match expected columns; inserted standard headers"
        )

    def _append_csv_row(self, row: list[str | int]) -> None:
        path = self._fallback_csv_path
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(HEADERS)
            writer.writerow(row)
        logger.info("Appended row to CSV fallback → %s", path)

    def _write_csv_headers(self) -> None:
        path = self._fallback_csv_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(HEADERS)

    def _require_spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            raise RuntimeError("Google Sheets is not connected. Call connect() first.")
        return self._spreadsheet

    def _require_worksheet(self) -> gspread.Worksheet:
        if self._worksheet is None:
            raise RuntimeError(
                "Google Sheets worksheet is not ready. Call create_sheet_if_missing()."
            )
        return self._worksheet

    @staticmethod
    def _to_row(result: ExportRow) -> list[str | int]:
        if isinstance(result, BrandResearchResult):
            brand_fit: str | int = result.research.brand_fit
            confidence: str | int = result.research.confidence
            suggested_dm = result.research.first_outreach_angle
            notes = result.research.overall_summary
            status = "researched"
        else:
            brand_fit = ""
            confidence = ""
            suggested_dm = ""
            notes = result.analysis.reason
            status = "analysed"

        return [
            result.profile.name,
            result.profile.profile_url,
            result.profile.followers,
            result.analysis.score,
            brand_fit,
            confidence,
            result.analysis.comment,
            suggested_dm,
            status,
            notes,
        ]
