"""Investment Screener Engine — Day 15 deliverable.

DAD-PROJ-001 Sprint 3.

Loads screener_config.yaml, applies threshold filters to the
financial_ratios + market_cap data, computes composite quality scores,
and returns ranked DataFrames.

Key design decisions:
  - Financial sector companies are automatically excluded from D/E max
    filters (high leverage is structurally normal for banks/NBFCs).
  - ICR = None (Debt Free companies) passes any minimum ICR threshold.
  - Composite score uses P10/P90 winsorisation to prevent outliers from
    dominating the 0-100 scale.
  - All thresholds are defined in config/screener_config.yaml — no
    hardcoded values in this module.
"""

import logging
import os
import sys
from typing import Optional

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "screener_config.yaml")
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
SUPPORTING_DIR = os.path.join(PROJECT_ROOT, "data", "supporting")


def load_config() -> dict:
    """Load screener_config.yaml."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_screener_data() -> pd.DataFrame:
    """Load and merge financial_ratios + market_cap + sectors into one DataFrame.

    Returns one row per company (latest available year for each dataset).
    """
    # Financial ratios — latest year per company
    fr = pd.read_excel(
        os.path.join(SUPPORTING_DIR, "financial_ratios.xlsx"), header=0
    )
    fr["company_id"] = fr["company_id"].astype(str).str.strip().str.upper()
    fr = fr.sort_values("year").groupby("company_id").last().reset_index()

    # Pull CAGR columns from SQLite (computed by ratio_engine.py in Sprint 2)
    db_path = os.path.join(PROJECT_ROOT, "db", "nifty100.db")
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        try:
            cagr_df = pd.read_sql(
                """SELECT company_id, year,
                          revenue_cagr_5yr, pat_cagr_5yr, eps_cagr_5yr,
                          return_on_capital_pct
                   FROM financial_ratios""",
                conn
            )
            cagr_df["company_id"] = cagr_df["company_id"].astype(str).str.strip().str.upper()
            cagr_df = cagr_df.sort_values("year").groupby("company_id").last().reset_index()
            cagr_df = cagr_df.drop(columns=["year"])
            fr = fr.merge(cagr_df, on="company_id", how="left")
            logger.info("Merged CAGR columns from SQLite: %d companies.", len(cagr_df))
        except Exception as e:
            logger.warning("Could not load CAGR from SQLite: %s", e)
        finally:
            conn.close()

    # Market cap — latest year per company
    mc = pd.read_excel(
        os.path.join(SUPPORTING_DIR, "market_cap.xlsx"), header=0
    )
    mc["company_id"] = mc["company_id"].astype(str).str.strip().str.upper()
    mc = mc.sort_values("year").groupby("company_id").last().reset_index()
    mc_cols = ["company_id", "market_cap_crore", "pe_ratio", "pb_ratio",
               "ev_ebitda", "dividend_yield_pct"]
    mc = mc[mc_cols]

    # Sectors — for financial sector exclusion rule
    sectors = pd.read_excel(
        os.path.join(SUPPORTING_DIR, "sectors.xlsx"), header=0
    )
    sectors["company_id"] = sectors["company_id"].astype(str).str.strip().str.upper()
    sectors = sectors[["company_id", "broad_sector", "sub_sector"]]

    # P&L — for sales filter and revenue CAGR (latest year)
    pl = pd.read_excel(os.path.join(RAW_DIR, "profitandloss.xlsx"), header=1)
    pl["company_id"] = pl["company_id"].astype(str).str.strip().str.upper()
    pl = pl.sort_values("year").groupby("company_id").last().reset_index()
    pl_cols = ["company_id", "sales", "net_profit", "dividend_payout"]
    pl = pl[[c for c in pl_cols if c in pl.columns]]

    # Companies — for names
    companies = pd.read_excel(os.path.join(RAW_DIR, "companies.xlsx"), header=1)
    companies["id"] = companies["id"].astype(str).str.strip().str.upper()
    companies = companies[["id", "company_name"]].rename(columns={"id": "company_id"})

    # Merge everything
    df = fr.merge(mc, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(pl, on="company_id", how="left")
    df = df.merge(companies, on="company_id", how="left")

    logger.info("Screener data loaded: %d companies.", len(df))
    return df


def winsorise(series: pd.Series, p_low: float = 10, p_high: float = 90) -> pd.Series:
    """Cap values at P10 and P90 to prevent outliers dominating scores."""
    low = series.quantile(p_low / 100)
    high = series.quantile(p_high / 100)
    return series.clip(lower=low, upper=high)


def normalise_0_100(series: pd.Series) -> pd.Series:
    """Scale a series to 0-100 range after winsorisation."""
    ws = winsorise(series)
    rng = ws.max() - ws.min()
    if rng == 0:
        return pd.Series(50.0, index=series.index)
    return ((ws - ws.min()) / rng * 100).round(2)


def compute_composite_score(df: pd.DataFrame, config: dict) -> pd.Series:
    """Compute composite quality score (0-100) for each company.

    Weights per DAD-PROJ-001 Section 25.1:
      35% Profitability + 30% Cash Quality + 20% Growth + 15% Leverage
    """
    score = pd.Series(0.0, index=df.index)

    # Profitability (35%)
    if "return_on_equity_pct" in df.columns:
        score += normalise_0_100(df["return_on_equity_pct"].fillna(0)) * 0.15
    if "net_profit_margin_pct" in df.columns:
        score += normalise_0_100(df["net_profit_margin_pct"].fillna(0)) * 0.10
    if "return_on_capital_pct" in df.columns:
        score += normalise_0_100(df["return_on_capital_pct"].fillna(0)) * 0.10

    # Cash Quality (30%)
    if "cash_from_operations_cr" in df.columns:
        score += normalise_0_100(df["cash_from_operations_cr"].fillna(0)) * 0.10
    if "free_cash_flow_cr" in df.columns:
        fcf_flag = (df["free_cash_flow_cr"].fillna(0) > 0).astype(float) * 100
        score += fcf_flag * 0.05
        score += normalise_0_100(df["free_cash_flow_cr"].fillna(0)) * 0.15

    # Growth (20%)
    if "revenue_cagr_5yr" in df.columns:
        score += normalise_0_100(df["revenue_cagr_5yr"].fillna(0)) * 0.10
    if "pat_cagr_5yr" in df.columns:
        score += normalise_0_100(df["pat_cagr_5yr"].fillna(0)) * 0.10

    # Leverage (15%) — inverse: lower D/E = higher score
    if "debt_to_equity" in df.columns:
        de_inv = 1 / (df["debt_to_equity"].fillna(0) + 0.1)
        score += normalise_0_100(de_inv) * 0.10
    if "interest_coverage" in df.columns:
        score += normalise_0_100(df["interest_coverage"].fillna(0)) * 0.05

    return score.round(2)


def apply_filter(
    df: pd.DataFrame,
    column: str,
    operator: str,
    threshold: float,
    skip_financials: bool = False,
) -> pd.Series:
    """Apply a single filter and return a boolean mask.

    Args:
        df: Screener DataFrame.
        column: Column name to filter on.
        operator: 'min', 'max', or 'eq'.
        threshold: Threshold value.
        skip_financials: If True, Financial sector companies always pass
            this filter (used for D/E filters).

    Returns:
        Boolean Series — True = passes filter.
    """
    if column not in df.columns:
        logger.warning("Filter column '%s' not found in data — skipping.", column)
        return pd.Series(True, index=df.index)

    values = df[column].copy()

    # ICR: Debt Free (None/NaN) passes any minimum threshold
    if column == "interest_coverage" and operator == "min":
        icr_null_passes = values.isna()
    else:
        icr_null_passes = pd.Series(False, index=df.index)

    # Financial sector exclusion for D/E filters
    if skip_financials and "broad_sector" in df.columns:
        fin_mask = df["broad_sector"] == "Financials"
    else:
        fin_mask = pd.Series(False, index=df.index)

    # Apply operator — nulls fail min/eq filters, pass max filters
    if operator == "min":
        mask = (values.notna() & (values >= threshold)) | icr_null_passes
    elif operator == "max":
        mask = values.isna() | (values <= threshold)
    elif operator == "eq":
        mask = values == threshold
    else:
        logger.warning("Unknown operator '%s' — skipping filter.", operator)
        return pd.Series(True, index=df.index)

    # Financial sector companies always pass D/E filters
    return mask | fin_mask


def run_preset(
    df: pd.DataFrame,
    preset_name: str,
    config: dict,
) -> pd.DataFrame:
    """Run a named preset screener and return sorted results.

    Args:
        df: Full screener DataFrame with composite scores already computed.
        preset_name: Key in config['presets'].
        config: Loaded screener_config.yaml.

    Returns:
        Filtered and sorted DataFrame. Empty if no companies pass.
    """
    preset = config["presets"].get(preset_name)
    if not preset:
        raise ValueError(f"Unknown preset: {preset_name}")

    skip_de = config.get("financial_sector_rules", {}).get(
        "skip_de_filter_for_financials", True
    )

    mask = pd.Series(True, index=df.index)

    for column, rules in preset["filters"].items():
        for operator, threshold in rules.items():
            is_de_filter = column == "debt_to_equity"
            col_mask = apply_filter(
                df, column, operator, threshold,
                skip_financials=skip_de and is_de_filter,
            )
            mask = mask & col_mask

    result = df[mask].copy()

    ranking_metric = preset.get("ranking_metric", "composite_quality_score")
    ranking_order = preset.get("ranking_order", "desc")
    ascending = ranking_order == "asc"

    if ranking_metric in result.columns:
        result = result.sort_values(ranking_metric, ascending=ascending)

    logger.info(
        "Preset '%s': %d companies passed filters.", preset_name, len(result)
    )
    return result.reset_index(drop=True)


def run_all_presets(
    df: Optional[pd.DataFrame] = None,
    config: Optional[dict] = None,
) -> dict:
    """Run all 6 preset screeners and return results as a dict.

    Args:
        df: Pre-loaded screener DataFrame. If None, loads from files.
        config: Pre-loaded config. If None, loads from YAML.

    Returns:
        Dict mapping preset_name -> filtered DataFrame.
    """
    if config is None:
        config = load_config()
    if df is None:
        df = load_screener_data()
        df["composite_quality_score"] = compute_composite_score(df, config)

    results = {}
    for preset_name in config["presets"]:
        results[preset_name] = run_preset(df, preset_name, config)

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    print("Loading screener data...")
    config = load_config()
    df = load_screener_data()
    df["composite_quality_score"] = compute_composite_score(df, config)

    print(f"\nTotal companies in screener universe: {len(df)}")
    print(f"Composite score range: {df['composite_quality_score'].min():.1f} — {df['composite_quality_score'].max():.1f}")

    print("\nRunning 6 preset screeners...")
    results = run_all_presets(df, config)

    print("\nResults:")
    for name, result_df in results.items():
        status = "✓" if 5 <= len(result_df) <= 50 else "⚠"
        print(f"  {status} {name}: {len(result_df)} companies")
        if len(result_df) > 0:
            cols = ["company_id", "company_name", "composite_quality_score"]
            available = [c for c in cols if c in result_df.columns]
            print(result_df[available].head(3).to_string(index=False))
        print()
