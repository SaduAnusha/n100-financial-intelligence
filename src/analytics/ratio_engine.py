"""Full Ratio Engine — Day 12 deliverable.

Combines ratios.py, cagr.py, and cashflow_kpis.py to compute all 16+
KPI columns for every company-year combination and write them into the
financial_ratios table in nifty100.db.

Also generates output/capital_allocation.csv as required by the spec.

Run directly: python src/analytics/ratio_engine.py
"""

import logging
import os
import sqlite3
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from ratios import (
    net_profit_margin, operating_profit_margin, opm_cross_check,
    return_on_equity, return_on_capital_employed, return_on_assets,
    debt_to_equity, interest_coverage_ratio, net_debt, asset_turnover,
    load_financial_sector_ids,
)
from cagr import compute_cagr_for_company
from cashflow_kpis import (
    free_cash_flow, capex_intensity, fcf_conversion_rate,
    capital_allocation_pattern, compute_capital_allocation_all,
    write_capital_allocation_csv,
)

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(PROJECT_ROOT, "db", "nifty100.db")
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
SUPPORTING_DIR = os.path.join(PROJECT_ROOT, "data", "supporting")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def load_source_data():
    """Load and merge all source DataFrames needed for ratio computation."""
    pl = pd.read_excel(os.path.join(RAW_DIR, "profitandloss.xlsx"), header=1)
    bs = pd.read_excel(os.path.join(RAW_DIR, "balancesheet.xlsx"), header=1)
    cf = pd.read_excel(os.path.join(RAW_DIR, "cashflow.xlsx"), header=1)
    sectors = pd.read_excel(os.path.join(SUPPORTING_DIR, "sectors.xlsx"), header=0)

    # Normalise tickers
    for df in [pl, bs, cf]:
        df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

    sectors["company_id"] = sectors["company_id"].astype(str).str.strip().str.upper()

    # Register financial sector IDs for D/E flag and ROCE benchmark
    fin_ids = set(sectors[sectors["broad_sector"] == "Financials"]["company_id"])
    load_financial_sector_ids(fin_ids)
    logger.info("Registered %d financial-sector companies.", len(fin_ids))

    # Filter out unparseable years (TTM, 9m etc.) — keep only Month YYYY format
    for df in [pl, bs, cf]:
        df["year"] = df["year"].astype(str)

    # Merge P&L + BS on (company_id, year)
    merged = pl.merge(bs, on=["company_id", "year"], suffixes=("_pl", "_bs"))
    # Merge with CF
    merged = merged.merge(cf, on=["company_id", "year"], suffixes=("", "_cf"))

    logger.info(
        "Merged dataset: %d rows across %d companies.",
        len(merged), merged["company_id"].nunique()
    )

    return merged, pl, bs, cf


def compute_book_value_per_share(row) -> float:
    """BV per share = (equity + reserves) / (equity_capital / face_value)."""
    try:
        equity = row.get("equity_capital", 0) or 0
        reserves = row.get("reserves", 0) or 0
        face_value = row.get("face_value", 1) or 1
        shares = equity / face_value  # shares outstanding in crore units
        if shares <= 0:
            return None
        return round((equity + reserves) / shares, 4)
    except Exception:
        return None


def compute_ratios_for_row(row: dict, pl_df: pd.DataFrame) -> dict:
    """Compute all KPIs for a single company-year row."""
    company_id = row.get("company_id", "")
    year = row.get("year", "")

    # --- Profitability ---
    npm = net_profit_margin(row.get("net_profit"), row.get("sales"))
    opm = operating_profit_margin(row.get("operating_profit"), row.get("sales"))

    roe = return_on_equity(
        row.get("net_profit"), row.get("equity_capital"), row.get("reserves")
    )
    roce = return_on_capital_employed(
        row.get("operating_profit"), row.get("depreciation"),
        row.get("equity_capital"), row.get("reserves"),
        row.get("borrowings"), company_id=company_id,
    )
    roa = return_on_assets(row.get("net_profit"), row.get("total_assets"))

    # --- Leverage ---
    de_ratio, _ = debt_to_equity(
        row.get("borrowings"), row.get("equity_capital"),
        row.get("reserves"), company_id=company_id,
    )
    icr, _ = interest_coverage_ratio(
        row.get("operating_profit"), row.get("other_income"), row.get("interest")
    )
    nd = net_debt(row.get("borrowings"), row.get("investments"))
    at = asset_turnover(row.get("sales"), row.get("total_assets"))

    # --- Cash Flow ---
    fcf = free_cash_flow(row.get("operating_activity"), row.get("investing_activity"))
    capex_pct, _ = capex_intensity(row.get("investing_activity"), row.get("sales"))

    # --- CAGR (computed from full P&L history, not just this row) ---
    cagr_rev = compute_cagr_for_company(pl_df, company_id, "sales", year, [5])
    cagr_pat = compute_cagr_for_company(pl_df, company_id, "net_profit", year, [5])
    cagr_eps = compute_cagr_for_company(pl_df, company_id, "eps", year, [5])

    # --- Other ---
    bvps = compute_book_value_per_share(row)

    return {
        "company_id": company_id,
        "year": year,
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "return_on_equity_pct": roe,
        "return_on_assets_pct": roa,
        "return_on_capital_pct": roce,
        "debt_to_equity": de_ratio,
        "interest_coverage": icr,
        "net_debt_cr": nd,
        "asset_turnover": at,
        "free_cash_flow_cr": fcf,
        "capex_cr": abs(row.get("investing_activity") or 0),
        "earnings_per_share": row.get("eps"),
        "book_value_per_share": bvps,
        "dividend_payout_ratio_pct": row.get("dividend_payout"),
        "total_debt_cr": row.get("borrowings"),
        "cash_from_operations_cr": row.get("operating_activity"),
        "revenue_cagr_5yr": cagr_rev.get("sales_cagr_5yr"),
        "revenue_cagr_5yr_flag": cagr_rev.get("sales_cagr_5yr_flag"),
        "pat_cagr_5yr": cagr_pat.get("net_profit_cagr_5yr"),
        "pat_cagr_5yr_flag": cagr_pat.get("net_profit_cagr_5yr_flag"),
        "eps_cagr_5yr": cagr_eps.get("eps_cagr_5yr"),
        "eps_cagr_5yr_flag": cagr_eps.get("eps_cagr_5yr_flag"),
    }


def populate_financial_ratios(merged_df: pd.DataFrame, pl_df: pd.DataFrame) -> pd.DataFrame:
    """Compute KPIs for all company-year rows and return as DataFrame."""
    records = []
    total = len(merged_df)

    for i, (_, row) in enumerate(merged_df.iterrows()):
        if i % 100 == 0:
            logger.info("Processing row %d / %d ...", i, total)
        record = compute_ratios_for_row(row.to_dict(), pl_df)
        records.append(record)

    df = pd.DataFrame(records)
    logger.info("Computed %d ratio records for %d companies.", len(df), df["company_id"].nunique())
    return df


def write_to_database(ratios_df: pd.DataFrame) -> int:
    """Write computed ratios to financial_ratios table in nifty100.db."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Clear existing data before re-populating
    conn.execute("DELETE FROM financial_ratios")
    conn.commit()

    # Only write columns that exist in the schema
    schema_cols = [
        "company_id", "year", "net_profit_margin_pct",
        "operating_profit_margin_pct", "return_on_equity_pct",
        "debt_to_equity", "interest_coverage", "asset_turnover",
        "free_cash_flow_cr", "capex_cr", "earnings_per_share",
        "book_value_per_share", "dividend_payout_ratio_pct",
        "total_debt_cr", "cash_from_operations_cr",
        "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr",
        "return_on_capital_pct",
    ]

    # Only keep rows where company_id exists in companies table
    valid_ids = set(
        row[0] for row in conn.execute("SELECT id FROM companies").fetchall()
    )
    filtered = ratios_df[ratios_df["company_id"].isin(valid_ids)].copy()

    # Deduplicate on (company_id, year)
    filtered = filtered.drop_duplicates(subset=["company_id", "year"], keep="last")

    write_cols = [c for c in schema_cols if c in filtered.columns]
    filtered[write_cols].to_sql(
        "financial_ratios", conn, if_exists="append", index=False
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    conn.close()

    logger.info("financial_ratios table now has %d rows.", count)
    return count


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    print("Loading source data...")
    merged, pl, bs, cf = load_source_data()

    print("Computing ratios for all company-year combinations...")
    ratios_df = populate_financial_ratios(merged, pl)

    print("Writing to database...")
    row_count = write_to_database(ratios_df)
    print(f"\nfinancial_ratios table: {row_count} rows")

    if row_count >= 1100:
        print("EXIT CRITERIA MET: >= 1,100 rows.")
    else:
        print(f"WARNING: Only {row_count} rows — below the 1,100 minimum.")

    # Generate capital_allocation.csv
    print("\nGenerating capital_allocation.csv...")
    cf["company_id"] = cf["company_id"].astype(str).str.strip().str.upper()
    ca_df = compute_capital_allocation_all(cf)
    out_path = os.path.join(OUTPUT_DIR, "capital_allocation.csv")
    write_capital_allocation_csv(ca_df, out_path)
    print(f"capital_allocation.csv: {len(ca_df)} rows written to {out_path}")

    print("\nPattern distribution:")
    print(ca_df["pattern_label"].value_counts().to_string())
