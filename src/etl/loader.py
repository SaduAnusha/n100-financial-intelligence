"""Excel loader for the N100 Financial Intelligence Platform.

Reads all 7 core source datasets from data/raw/, applies year and ticker
normalisation via src/etl/normaliser.py, and returns clean pandas
DataFrames ready for schema validation (Day 3) and SQLite loading (Day 4-5).

Per DAD-PROJ-001 Section 5 (Dataset Catalogue):
  - Core files use header=1 (row 0 is metadata, row 1 is the real header).
  - Supplementary files use header=0 (handled separately, Day 5).

Rows with an unparseable year or ticker are NOT silently dropped — they
are logged to parse_failures.csv so nothing is lost without a trace.
"""

import csv
import logging
import os
from typing import Dict, Optional

import pandas as pd

from normaliser import normalize_year, normalize_ticker

logger = logging.getLogger(__name__)

# Core files use header=1 per the spec's load note (Section 5).
# Maps logical dataset name -> (filename, has_year_column).
CORE_FILES: Dict[str, Dict] = {
    "companies": {"filename": "companies.xlsx", "id_col": "id", "has_year": False},
    "profitandloss": {"filename": "profitandloss.xlsx", "id_col": "company_id", "has_year": True},
    "balancesheet": {"filename": "balancesheet.xlsx", "id_col": "company_id", "has_year": True},
    "cashflow": {"filename": "cashflow.xlsx", "id_col": "company_id", "has_year": True},
    "analysis": {"filename": "analysis.xlsx", "id_col": "company_id", "has_year": False},
    "documents": {"filename": "documents.xlsx", "id_col": "company_id", "has_year": False, "year_col": "Year"},
    "prosandcons": {"filename": "prosandcons.xlsx", "id_col": "company_id", "has_year": False},
}

CORE_HEADER_ROW = 1  # row 0 is metadata; row 1 is the real header.


def load_excel_core(
    raw_dir: str,
    dataset_name: str,
    parse_failures: Optional[list] = None,
) -> pd.DataFrame:
    """Load and normalise a single core Excel dataset.

    Args:
        raw_dir: Path to the data/raw/ directory containing the source
            Excel files.
        dataset_name: One of the keys in CORE_FILES (e.g. "profitandloss").
        parse_failures: Optional list to append failure records to, in the
            form (dataset_name, company_id, raw_year, reason). If None,
            failures are only logged, not collected.

    Returns:
        A normalised DataFrame with company_id (and year, where
        applicable) standardised. Rows that fail normalisation are
        excluded from the returned DataFrame and recorded in
        parse_failures / the log.

    Raises:
        FileNotFoundError: if the source Excel file does not exist.
        KeyError: if dataset_name is not a recognised core dataset.
    """
    if dataset_name not in CORE_FILES:
        raise KeyError(f"Unknown core dataset: {dataset_name}")

    config = CORE_FILES[dataset_name]
    path = os.path.join(raw_dir, config["filename"])

    if not os.path.exists(path):
        raise FileNotFoundError(f"Core dataset not found: {path}")

    df = pd.read_excel(path, header=CORE_HEADER_ROW)
    rows_in = len(df)

    id_col = config["id_col"]
    df["_normalised_id"] = df[id_col].apply(normalize_ticker)

    bad_id_mask = df["_normalised_id"].isna()
    for _, row in df[bad_id_mask].iterrows():
        reason = "TICKER_PARSE_ERROR"
        if parse_failures is not None:
            parse_failures.append((dataset_name, row.get(id_col), None, reason))
        logger.warning("%s: rejected row, bad ticker value=%r", dataset_name, row.get(id_col))

    df = df[~bad_id_mask].copy()
    df[id_col] = df["_normalised_id"]
    df = df.drop(columns=["_normalised_id"])

    # Normalise the year column if this dataset has one.
    year_col = config.get("year_col", "year") if config["has_year"] or "year_col" in config else None
    if year_col and year_col in df.columns:
        df["_normalised_year"] = df[year_col].apply(normalize_year)

        bad_year_mask = df["_normalised_year"].isna()
        for _, row in df[bad_year_mask].iterrows():
            reason = "YEAR_PARSE_ERROR"
            if parse_failures is not None:
                parse_failures.append(
                    (dataset_name, row.get(id_col), row.get(year_col), reason)
                )
            logger.warning(
                "%s: rejected row, company_id=%s, bad year value=%r",
                dataset_name, row.get(id_col), row.get(year_col),
            )

        df = df[~bad_year_mask].copy()
        df[year_col] = df["_normalised_year"]
        df = df.drop(columns=["_normalised_year"])

    rows_out = len(df)
    logger.info(
        "%s: loaded %d rows, %d passed normalisation, %d rejected",
        dataset_name, rows_in, rows_out, rows_in - rows_out,
    )

    return df.reset_index(drop=True)


def load_all_core_files(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """Load and normalise all 7 core Excel datasets.

    Args:
        raw_dir: Path to the data/raw/ directory.

    Returns:
        A dict mapping dataset name -> normalised DataFrame.
    """
    parse_failures: list = []
    results = {}

    for dataset_name in CORE_FILES:
        results[dataset_name] = load_excel_core(raw_dir, dataset_name, parse_failures)

    if parse_failures:
        _write_parse_failures(raw_dir, parse_failures)

    return results


def _write_parse_failures(raw_dir: str, parse_failures: list) -> None:
    """Write rejected rows to parse_failures.csv in the output/ directory."""
    output_dir = os.path.join(os.path.dirname(raw_dir.rstrip("/").rstrip("\\")), "..", "output")
    output_dir = os.path.normpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "parse_failures.csv")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["dataset", "company_id", "raw_year", "reason"])
        writer.writerows(parse_failures)

    logger.info("Wrote %d parse failures to %s", len(parse_failures), out_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Resolve data/raw relative to this file's location: src/etl/loader.py -> ../../data/raw
    here = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.normpath(os.path.join(here, "..", "..", "data", "raw"))

    print(f"Loading core datasets from: {raw_dir}")
    dataframes = load_all_core_files(raw_dir)

    print("\nLoad summary:")
    for name, df in dataframes.items():
        print(f"  {name}: {len(df)} rows, {len(df.columns)} columns")
