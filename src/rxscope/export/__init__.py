"""Whitelist export — CSV/XLSX per RxNetwork output specification."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import structlog

log = structlog.get_logger()

# Required columns per client spec
REQUIRED_COLUMNS = [
    "url",
    "source_domain",
    "content_type",
    "detected_medical_categories",
    "detected_entity_associations",
    "confidence_score",
]

EXTENDED_COLUMNS = [
    "audience_type",
    "source_type",
]


def export_whitelist(entries: list[dict], output_path: str, fmt: str = "xlsx") -> Path:
    """Export whitelist entries to CSV or XLSX.

    Args:
        entries: List of whitelist dicts (from db.queries.get_whitelist_entries or pipeline output).
        output_path: Destination file path.
        fmt: "xlsx" or "csv".

    Returns:
        Path to the written file.
    """
    path = Path(output_path)
    all_columns = REQUIRED_COLUMNS + EXTENDED_COLUMNS
    df = pd.DataFrame(entries, columns=all_columns)

    # Ensure all required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df.sort_values("confidence_score", ascending=False).reset_index(drop=True)

    if fmt == "xlsx":
        if not path.suffix:
            path = path.with_suffix(".xlsx")
        df.to_excel(str(path), index=False, engine="openpyxl")
    else:
        if not path.suffix:
            path = path.with_suffix(".csv")
        df.to_csv(str(path), index=False)

    log.info("export.done", path=str(path), rows=len(df), format=fmt)
    return path
