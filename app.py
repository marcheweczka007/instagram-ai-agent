"""Streamlit entrypoint for the daily marketing workspace.

Run:
    uv run streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure `src/` is on the path when launched via `streamlit run app.py`.
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from instagram_agent.ui.main import render_app

render_app()
