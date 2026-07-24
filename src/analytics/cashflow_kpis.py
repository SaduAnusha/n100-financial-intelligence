"""Cash Flow Intelligence Module for the N100 Financial Intelligence Platform.

Day 11 deliverable (DAD-PROJ-001 Sprint 2).

Implements:
  - Free Cash Flow (FCF)
  - CFO Quality Score (CFO/PAT ratio, 5yr average)
  - CapEx Intensity (abs(investing_activity) / sales * 100)
  - FCF Conversion Rate (FCF / operating_profit * 100)
  - Capital Allocation 8-pattern classifier (CFO/CFI/CFF sign patterns)

All functions are pure (no I/O) and return None instead of
infinity/NaN for division-by-zero cases.
"""

import csv
import os
from typing import Optional, List, Dict
import pandas as pd

# ---------------------------------------------------------------------------
# Capital Allocation Pattern Labels
# ---------------------------------------------------------------------------
PATTERN_LABELS = {
    "(+,-,-)": "Reinvestor",
    "(+,+,-)": "Liquidating Assets",
    "(+,-,+)": "Mixed",
    "(+,+,+)": "Cash Accumulator",
    "(-,-,+)": "Growth Funded by Debt",
    "(-,+,+)": "Distress Signal",
    "(-,+,-)": "Asset Sale Survival",
    "(-,-,-)": "Pre-Revenue / Distress",
}

# CFO Quality Score tiers
CFO_QUALITY_HIGH = "High Quality"
CFO_QUALITY_MODERATE = "Moderate"
CFO_QUALITY_ACCRUAL_RISK = "Accrual Risk"

# CapEx Intensity tiers
CAPEX_ASSET_LIGHT = "Asset Light"
CAPEX_MODERATE = "Moderate"
CAPEX_CAPITAL_INTENSIVE = "Capital Intensive"


# ---------------------------------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------------------------------
def free_cash_flow(
    operating_activity: Optional[float],
    investing_activity: Optional[float],
) -> Optional[float]:
    """Compute Free Cash Flow: CFO + CFI.

    Negative FCF is allowed — it means the company is consuming more
    cash than it generates from operations after capital expenditure.

    Args:
        operating_activity: CFO in ₹ Crore.
        investing_activity: CFI in ₹ Crore (typically negative).

    Returns:
        FCF in ₹ Crore, or None if either input is None.
    """
    if operating_activity is None or investing_activity is None:
        return None
    return round(operating_activity + investing_activity, 4)


# ---------------------------------------------------------------------------
# CFO Quality Score
# ---------------------------------------------------------------------------
def cfo_quality_score(
    cfo_values: List[Optional[float]],
    pat_values: List[Optional[float]],
) -> tuple:
    """Compute CFO Quality Score: avg(CFO/PAT) over available years.

    A ratio > 1.0 means the company is converting more than 100% of its
    reported profit into actual cash — indicating high-quality earnings.
    A ratio < 0.5 suggests accrual-based accounting that may not hold up.

    Args:
        cfo_values: List of CFO values (₹ Crore) for up to 5 years.
        pat_values: List of PAT values (₹ Crore) for the same years.

    Returns:
        Tuple of (score: float | None, label: str).
        score is None if no valid CFO/PAT pairs exist.
    """
    ratios = []
    for cfo, pat in zip(cfo_values, pat_values):
        if cfo is None or pat is None or pat == 0:
            continue
        ratios.append(cfo / pat)

    if not ratios:
        return None, "N/A"

    avg_ratio = sum(ratios) / len(ratios)
    avg_ratio = round(avg_ratio, 4)

    if avg_ratio > 1.0:
        label = CFO_QUALITY_HIGH
    elif avg_ratio >= 0.5:
        label = CFO_QUALITY_MODERATE
    else:
        label = CFO_QUALITY_ACCRUAL_RISK

    return avg_ratio, label


# ---------------------------------------------------------------------------
# CapEx Intensity
# ---------------------------------------------------------------------------
def capex_intensity(
    investing_activity: Optional[float],
    sales: Optional[float],
) -> tuple:
    """Compute CapEx Intensity: abs(investing_activity) / sales * 100.

    Uses investing_activity as a CapEx proxy per the spec (Section 7.2).
    Asset-light companies (IT, FMCG) typically show < 3%.
    Capital-intensive companies (Steel, Power, Telecom) show > 8%.

    Args:
        investing_activity: CFI in ₹ Crore. Typically negative.
        sales: Net revenue in ₹ Crore. Must be > 0.

    Returns:
        Tuple of (intensity_pct: float | None, label: str).
    """
    if investing_activity is None or sales is None or sales == 0:
        return None, "N/A"

    intensity = round(abs(investing_activity) / sales * 100, 4)

    if intensity < 3.0:
        label = CAPEX_ASSET_LIGHT
    elif intensity <= 8.0:
        label = CAPEX_MODERATE
    else:
        label = CAPEX_CAPITAL_INTENSIVE

    return intensity, label


# ---------------------------------------------------------------------------
# FCF Conversion Rate
# ---------------------------------------------------------------------------
def fcf_conversion_rate(
    fcf: Optional[float],
    operating_profit: Optional[float],
) -> Optional[float]:
    """Compute FCF Conversion Rate: FCF / operating_profit * 100.

    > 60% = efficient cash conversion
    < 30% = heavy CapEx or working capital drag

    Args:
        fcf: Free Cash Flow in ₹ Crore.
        operating_profit: EBITDA in ₹ Crore. Must be non-zero.

    Returns:
        FCF conversion rate as a percentage, or None if inputs are
        missing or operating_profit is zero.
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return round(fcf / operating_profit * 100, 4)


# ---------------------------------------------------------------------------
# Capital Allocation Pattern Classifier
# ---------------------------------------------------------------------------
def _sign(value: Optional[float]) -> Optional[str]:
    """Return '+' for positive, '-' for negative/zero, None if missing."""
    if value is None:
        return None
    return "+" if value > 0 else "-"


def capital_allocation_pattern(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
) -> tuple:
    """Classify capital allocation based on signs of CFO, CFI, CFF.

    8 possible patterns per the spec's capital allocation matrix.

    Args:
        cfo: Cash Flow from Operations in ₹ Crore.
        cfi: Cash Flow from Investing in ₹ Crore.
        cff: Cash Flow from Financing in ₹ Crore.

    Returns:
        Tuple of (cfo_sign, cfi_sign, cff_sign, pattern_key, pattern_label).
        pattern_label is 'Unknown' if any sign is None.
    """
    cfo_sign = _sign(cfo)
    cfi_sign = _sign(cfi)
    cff_sign = _sign(cff)

    if None in (cfo_sign, cfi_sign, cff_sign):
        return cfo_sign, cfi_sign, cff_sign, "N/A", "Unknown"

    pattern_key = f"({cfo_sign},{cfi_sign},{cff_sign})"
    label = PATTERN_LABELS.get(pattern_key, "Unknown")

    return cfo_sign, cfi_sign, cff_sign, pattern_key, label


# ---------------------------------------------------------------------------
# Batch computation for all companies
# ---------------------------------------------------------------------------
def compute_capital_allocation_all(
    cf_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute capital allocation pattern for every company-year row.

    Args:
        cf_df: Normalised cashflow DataFrame with columns:
               company_id, year, operating_activity,
               investing_activity, financing_activity.

    Returns:
        DataFrame with columns: company_id, year, cfo_sign, cfi_sign,
        cff_sign, pattern_label.
    """
    records = []
    for _, row in cf_df.iterrows():
        cfo_sign, cfi_sign, cff_sign, _, label = capital_allocation_pattern(
            row.get("operating_activity"),
            row.get("investing_activity"),
            row.get("financing_activity"),
        )
        records.append({
            "company_id": row["company_id"],
            "year": row["year"],
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern_label": label,
        })
    return pd.DataFrame(records)


def write_capital_allocation_csv(df: pd.DataFrame, output_path: str) -> None:
    """Write capital allocation results to output/capital_allocation.csv."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    here = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.normpath(os.path.join(here, "..", "..", "data", "raw"))
    output_dir = os.path.normpath(os.path.join(here, "..", "..", "output"))

    cf = pd.read_excel(os.path.join(raw_dir, "cashflow.xlsx"), header=1)
    pl = pd.read_excel(os.path.join(raw_dir, "profitandloss.xlsx"), header=1)

    print("Computing capital allocation patterns...")
    ca_df = compute_capital_allocation_all(cf)

    out_path = os.path.join(output_dir, "capital_allocation.csv")
    write_capital_allocation_csv(ca_df, out_path)
    print(f"Written to {out_path}")
    print(f"Total rows: {len(ca_df)}")
    print("\nPattern distribution:")
    print(ca_df["pattern_label"].value_counts())

    print("\nSample TCS:")
    print(ca_df[ca_df["company_id"] == "TCS"].tail(3))
