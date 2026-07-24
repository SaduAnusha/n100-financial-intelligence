"""CAGR Engine for the N100 Financial Intelligence Platform.

Day 10 deliverable (DAD-PROJ-001 Sprint 2).

Computes Compound Annual Growth Rate (CAGR) for:
  - Revenue (sales)
  - PAT (net_profit)
  - EPS

For 3-year, 5-year, and 10-year windows.

All 6 edge cases from DAD-PROJ-001 Section 23.1 are handled:
  NORMAL          — base > 0, end > 0 → compute normally
  DECLINE_TO_LOSS — base > 0, end < 0 → return None, flag
  TURNAROUND      — base < 0, end > 0 → return None, flag
  BOTH_NEGATIVE   — base < 0, end < 0 → return None, flag
  ZERO_BASE       — base = 0          → return None, flag
  INSUFFICIENT    — fewer than n years → return None, flag

Each CAGR result is returned alongside a flag string stored in a
separate column (e.g. revenue_cagr_5yr_flag) so downstream modules
can distinguish between a genuine 0% CAGR and an uncomputable case.
"""

from typing import Optional, Tuple
import pandas as pd

# ---------------------------------------------------------------------------
# Edge case flag constants
# ---------------------------------------------------------------------------
FLAG_NORMAL = "NORMAL"
FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"


def compute_cagr(
    start_value: Optional[float],
    end_value: Optional[float],
    n_years: int,
) -> Tuple[Optional[float], str]:
    """Compute CAGR for a single start/end value pair.

    Formula: ((end / start) ^ (1/n)) - 1) * 100

    Args:
        start_value: Value at the beginning of the period. Can be
            negative (loss) or zero.
        end_value: Value at the end of the period. Can be negative.
        n_years: Number of years in the CAGR window (3, 5, or 10).

    Returns:
        Tuple of (cagr_pct: float | None, flag: str).
        cagr_pct is None for all edge cases except NORMAL.
        flag is one of the FLAG_* constants above.
    """
    # Missing data
    if start_value is None or end_value is None:
        return None, FLAG_INSUFFICIENT

    # Zero base — division by zero
    if start_value == 0:
        return None, FLAG_ZERO_BASE

    # Both negative — mathematically undefined / meaningless
    if start_value < 0 and end_value < 0:
        return None, FLAG_BOTH_NEGATIVE

    # Turnaround — base negative, end positive
    if start_value < 0 and end_value > 0:
        return None, FLAG_TURNAROUND

    # Decline to loss — base positive, end negative
    if start_value > 0 and end_value < 0:
        return None, FLAG_DECLINE_TO_LOSS

    # Normal case — both positive
    cagr = ((end_value / start_value) ** (1 / n_years) - 1) * 100
    return round(cagr, 4), FLAG_NORMAL


def get_value_for_year(
    df: pd.DataFrame,
    company_id: str,
    col: str,
    target_year: str,
) -> Optional[float]:
    """Retrieve a single value for a company in a specific year.

    Args:
        df: DataFrame containing company_id, year, and the target column.
        company_id: NSE ticker string.
        col: Column name to retrieve (e.g. 'sales', 'net_profit').
        target_year: Normalised year string ('YYYY-MM').

    Returns:
        The value as a float, or None if not found / null.
    """
    mask = (df["company_id"] == company_id) & (df["year"] == target_year)
    rows = df[mask]
    if rows.empty:
        return None
    val = rows.iloc[0][col]
    return None if pd.isna(val) else float(val)


def compute_cagr_for_company(
    df: pd.DataFrame,
    company_id: str,
    col: str,
    latest_year: str,
    windows: list = None,
) -> dict:
    """Compute CAGR for a given metric across multiple time windows.

    Args:
        df: DataFrame with company_id, year, and the metric column.
            Years must already be normalised to 'YYYY-MM' format.
        company_id: NSE ticker string.
        col: Column name for the metric (e.g. 'sales').
        latest_year: The most recent year for this company ('YYYY-MM').
        windows: List of year windows to compute (default: [3, 5, 10]).

    Returns:
        Dictionary with keys like 'sales_cagr_3yr', 'sales_cagr_3yr_flag',
        'sales_cagr_5yr', 'sales_cagr_5yr_flag', etc.
    """
    if windows is None:
        windows = [3, 5, 10]

    # Get sorted unique years for this company
    company_years = sorted(
        df[df["company_id"] == company_id]["year"].unique().tolist()
    )
    n_available = len(company_years)
    end_value = get_value_for_year(df, company_id, col, latest_year)

    results = {}
    for n in windows:
        key = f"{col}_cagr_{n}yr"
        flag_key = f"{col}_cagr_{n}yr_flag"

        # Not enough history for this window
        if n_available < n + 1:
            results[key] = None
            results[flag_key] = FLAG_INSUFFICIENT
            continue

        # Base year is n years before the latest available year
        base_year = company_years[-(n + 1)]
        start_value = get_value_for_year(df, company_id, col, base_year)

        cagr, flag = compute_cagr(start_value, end_value, n)
        results[key] = cagr
        results[flag_key] = flag

    return results


def compute_all_cagrs(
    pl_df: pd.DataFrame,
    windows: list = None,
) -> pd.DataFrame:
    """Compute Revenue, PAT, and EPS CAGRs for all companies.

    Args:
        pl_df: Normalised profitandloss DataFrame with columns:
               company_id, year, sales, net_profit, eps.
        windows: CAGR windows to compute (default: [3, 5, 10]).

    Returns:
        DataFrame with one row per company (latest year), containing
        company_id, year, and all CAGR columns with their flag columns.
    """
    if windows is None:
        windows = [3, 5, 10]

    metrics = {
        "sales": "revenue",
        "net_profit": "pat",
        "eps": "eps",
    }

    records = []
    for company_id in pl_df["company_id"].unique():
        company_df = pl_df[pl_df["company_id"] == company_id]
        latest_year = company_df["year"].max()

        record = {"company_id": company_id, "year": latest_year}

        for source_col, label in metrics.items():
            cagr_results = compute_cagr_for_company(
                pl_df, company_id, source_col, latest_year, windows
            )
            # Rename keys to use the friendly label (revenue/pat/eps)
            for n in windows:
                record[f"{label}_cagr_{n}yr"] = cagr_results.get(
                    f"{source_col}_cagr_{n}yr"
                )
                record[f"{label}_cagr_{n}yr_flag"] = cagr_results.get(
                    f"{source_col}_cagr_{n}yr_flag"
                )

        records.append(record)

    return pd.DataFrame(records)


if __name__ == "__main__":
    import os
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    here = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.normpath(os.path.join(here, "..", "..", "data", "raw"))

    pl = pd.read_excel(os.path.join(raw_dir, "profitandloss.xlsx"), header=1)

    # Filter out unparseable years (TTM etc.)
    pl = pl[pl["year"].astype(str).str.match(r"^[A-Za-z]+ \d{4}$")]
    pl["year"] = pl["year"].astype(str)

    print("Computing CAGRs for all companies...")
    result = compute_all_cagrs(pl)

    print(f"\nCAGR table shape: {result.shape}")
    print("\nSample (TCS):")
    tcs = result[result["company_id"] == "TCS"]
    if not tcs.empty:
        for col in tcs.columns:
            print(f"  {col}: {tcs.iloc[0][col]}")
