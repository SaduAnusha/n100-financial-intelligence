"""Valuation Module — Day 26 deliverable.

DAD-PROJ-001 Sprint 4.

Computes:
  - FCF Yield: FCF / market_cap_crore * 100
  - Sector median P/E
  - Overvaluation flags: Caution / Discount / Fair
  - Generates valuation_summary.xlsx and valuation_flags.csv
"""

import logging
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

logger = logging.getLogger(__name__)

SUPPORTING_DIR = os.path.join(PROJECT_ROOT, "data", "supporting")
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def load_valuation_data() -> pd.DataFrame:
    """Load and merge market_cap, financial_ratios, sectors, and companies."""
    mc = pd.read_excel(os.path.join(SUPPORTING_DIR, "market_cap.xlsx"), header=0)
    mc["company_id"] = mc["company_id"].astype(str).str.strip().str.upper()
    mc_latest = mc.sort_values("year").groupby("company_id").last().reset_index()

    fr = pd.read_excel(os.path.join(SUPPORTING_DIR, "financial_ratios.xlsx"), header=0)
    fr["company_id"] = fr["company_id"].astype(str).str.strip().str.upper()
    fr_latest = fr.sort_values("year").groupby("company_id").last().reset_index()
    fr_latest = fr_latest[["company_id", "free_cash_flow_cr"]]

    sectors = pd.read_excel(os.path.join(SUPPORTING_DIR, "sectors.xlsx"), header=0)
    sectors["company_id"] = sectors["company_id"].astype(str).str.strip().str.upper()
    sectors = sectors[["company_id", "broad_sector", "sub_sector"]]

    companies = pd.read_excel(os.path.join(RAW_DIR, "companies.xlsx"), header=1)
    companies["id"] = companies["id"].astype(str).str.strip().str.upper()
    companies = companies[["id", "company_name"]].rename(columns={"id": "company_id"})

    df = mc_latest.merge(fr_latest, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, on="company_id", how="left")

    return df


def compute_fcf_yield(df: pd.DataFrame) -> pd.DataFrame:
    """FCF Yield = FCF / market_cap_crore * 100."""
    df = df.copy()
    mask = df["market_cap_crore"].notna() & (df["market_cap_crore"] > 0) & df["free_cash_flow_cr"].notna()
    df["fcf_yield_pct"] = None
    df.loc[mask, "fcf_yield_pct"] = (
        df.loc[mask, "free_cash_flow_cr"] / df.loc[mask, "market_cap_crore"] * 100
    ).round(4)
    return df


def compute_sector_median_pe(df: pd.DataFrame) -> pd.DataFrame:
    """Compute sector median P/E and add as a column."""
    sector_med = df.groupby("broad_sector")["pe_ratio"].median().reset_index()
    sector_med.columns = ["broad_sector", "sector_median_pe"]
    df = df.merge(sector_med, on="broad_sector", how="left")
    return df


def apply_valuation_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Caution / Discount / Fair flags based on P/E vs sector median."""
    df = df.copy()
    df["valuation_flag"] = "Fair"

    caution_mask = (
        df["pe_ratio"].notna() &
        df["sector_median_pe"].notna() &
        (df["pe_ratio"] > df["sector_median_pe"] * 1.5)
    )
    discount_mask = (
        df["pe_ratio"].notna() &
        df["sector_median_pe"].notna() &
        (df["pe_ratio"] < df["sector_median_pe"] * 0.7)
    )

    df.loc[caution_mask, "valuation_flag"] = "Caution"
    df.loc[discount_mask, "valuation_flag"] = "Discount"

    df["pe_vs_sector_pct"] = None
    valid = df["sector_median_pe"].notna() & (df["sector_median_pe"] > 0) & df["pe_ratio"].notna()
    df.loc[valid, "pe_vs_sector_pct"] = (
        (df.loc[valid, "pe_ratio"] - df.loc[valid, "sector_median_pe"]) /
        df.loc[valid, "sector_median_pe"] * 100
    ).round(2)

    return df


def compute_5yr_median_pe(mc: pd.DataFrame) -> pd.DataFrame:
    """Compute 5-year median P/E per company."""
    mc["company_id"] = mc["company_id"].astype(str).str.strip().str.upper()
    med_5yr = mc.groupby("company_id")["pe_ratio"].median().reset_index()
    med_5yr.columns = ["company_id", "pe_5yr_median"]
    return med_5yr


def generate_valuation_outputs() -> pd.DataFrame:
    """Main function — runs full valuation pipeline and writes output files."""
    df = load_valuation_data()
    df = compute_fcf_yield(df)
    df = compute_sector_median_pe(df)
    df = apply_valuation_flags(df)

    mc_all = pd.read_excel(os.path.join(SUPPORTING_DIR, "market_cap.xlsx"), header=0)
    med_5yr = compute_5yr_median_pe(mc_all)
    df = df.merge(med_5yr, on="company_id", how="left")

    # Build valuation_summary.xlsx
    summary_cols = [
        "company_id", "company_name", "broad_sector",
        "pe_ratio", "pb_ratio", "ev_ebitda",
        "fcf_yield_pct", "pe_5yr_median",
        "sector_median_pe", "pe_vs_sector_pct",
        "valuation_flag", "market_cap_crore",
        "dividend_yield_pct", "free_cash_flow_cr",
    ]
    summary = df[[c for c in summary_cols if c in df.columns]].copy()
    summary = summary.round(2)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary_path = os.path.join(OUTPUT_DIR, "valuation_summary.xlsx")
    summary.to_excel(summary_path, index=False)
    logger.info("Saved valuation_summary.xlsx: %d rows", len(summary))

    # Build valuation_flags.csv — only Caution and Discount
    flags = summary[summary["valuation_flag"].isin(["Caution", "Discount"])].copy()
    flags_path = os.path.join(OUTPUT_DIR, "valuation_flags.csv")
    flags.to_csv(flags_path, index=False)
    logger.info("Saved valuation_flags.csv: %d flagged companies", len(flags))

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("Running valuation module...")
    summary = generate_valuation_outputs()

    print(f"\nvaluation_summary.xlsx: {len(summary)} rows")
    print("\nFlag distribution:")
    print(summary["valuation_flag"].value_counts().to_string())

    print("\nTop 5 by FCF Yield:")
    fcf_data = summary.copy()
    fcf_data["fcf_yield_pct"] = pd.to_numeric(fcf_data["fcf_yield_pct"], errors="coerce")
    top_fcf = fcf_data.nlargest(5, "fcf_yield_pct")[
        ["company_id", "company_name", "fcf_yield_pct", "pe_ratio", "valuation_flag"]
    ]
    print(top_fcf.to_string(index=False))
