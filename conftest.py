"""Register step definitions and label the HTML report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytest_plugins = ["steps.booking_steps"]


def pytest_metadata(metadata: dict[str, object], config: object) -> None:
    """Add suite context to the pytest-html environment table."""

    del config
    metadata["Project"] = "pytest-bdd API workflows"
    metadata["Target API"] = "https://restful-booker.herokuapp.com"
    metadata["Suite"] = "portfolio demo"


def pytest_html_report_title(report) -> None:
    report.title = "Booking API workflows"
