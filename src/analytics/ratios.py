"""Financial Ratio Engine — Profitability & Returns Module.

Day 8 deliverable (DAD-PROJ-001 Sprint 2).

Implements the following KPIs:
  - Net Profit Margin (NPM)
  - Operating Profit Margin (OPM)
  - Return on Equity (ROE)
  - Return on Capital Employed (ROCE)
  - Return on Assets (ROA)

All functions are pure (no I/O, no database calls) so they are easy to
unit test in isolation. Each function takes scalar values and returns a
float or None. None is always returned instead of infinity or NaN so
downstream code never needs to handle division-by-zero silently.

Edge cases handled per DAD-PROJ-001 Section 13 (KPI Reference):
  - Zero denominator → None
  - Negative equity → None for ROE/ROCE
  - Financial sector companies → ROCE uses sector-relative benchmark
    (flag only; formula is the same, threshold differs)
  - OPM cross-check: computed value is compared against source field;
    discrepancies > 1% are flagged for logging
"""

from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Financial sector tickers — D/E warning suppressed; ROCE uses different
# benchmark (sector-relative rather than absolute >15% threshold).
# Populated from sectors.xlsx via the load_financial_sector_ids() helper.
# ---------------------------------------------------------------------------
_FINANCIAL_SECTOR_IDS: set = set()


def load_financial_sector_ids(sector_ids: set) -> None:
    """Register the set of Financial-sector company IDs.

    Call this once at startup before running batch ratio computation,
    passing the set of company_ids where broad_sector == 'Financials'.

    Args:
        sector_ids: Set of NSE ticker strings for financial-sector companies.
    """
    global _FINANCIAL_SECTOR_IDS
    _FINANCIAL_SECTOR_IDS = set(sector_ids)


def is_financial(company_id: str) -> bool:
    """Return True if the company is in the Financials broad_sector."""
    return company_id in _FINANCIAL_SECTOR_IDS


# ---------------------------------------------------------------------------
# Net Profit Margin
# ---------------------------------------------------------------------------
def net_profit_margin(
    net_profit: Optional[float],
    sales: Optional[float],
) -> Optional[float]:
    """Compute Net Profit Margin: net_profit / sales * 100.

    Args:
        net_profit: PAT in ₹ Crore. Negative values are allowed.
        sales: Net revenue in ₹ Crore. Must be > 0.

    Returns:
        NPM as a percentage, or None if sales is zero/null.
    """
    if net_profit is None or sales is None:
        return None
    if sales == 0:
        return None
    return round(net_profit / sales * 100, 4)


# ---------------------------------------------------------------------------
# Operating Profit Margin
# ---------------------------------------------------------------------------
def operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
) -> Optional[float]:
    """Compute Operating Profit Margin: operating_profit / sales * 100.

    Args:
        operating_profit: EBITDA in ₹ Crore.
        sales: Net revenue in ₹ Crore. Must be > 0.

    Returns:
        OPM as a percentage, or None if sales is zero/null.
    """
    if operating_profit is None or sales is None:
        return None
    if sales == 0:
        return None
    return round(operating_profit / sales * 100, 4)


def opm_cross_check(
    computed_opm: Optional[float],
    source_opm: Optional[float],
    tolerance: float = 1.0,
) -> Tuple[bool, Optional[float]]:
    """Cross-check computed OPM against the source opm_percentage field.

    Args:
        computed_opm: OPM computed from operating_profit / sales * 100.
        source_opm: opm_percentage value directly from the source file.
        tolerance: Maximum allowed difference in percentage points (default 1%).

    Returns:
        Tuple of (is_within_tolerance: bool, diff: float | None).
        If either value is None, returns (True, None) — no check possible.
    """
    if computed_opm is None or source_opm is None:
        return True, None
    diff = abs(computed_opm - source_opm)
    return diff <= tolerance, round(diff, 4)


# ---------------------------------------------------------------------------
# Return on Equity (ROE)
# ---------------------------------------------------------------------------
def return_on_equity(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
) -> Optional[float]:
    """Compute Return on Equity: net_profit / (equity_capital + reserves) * 100.

    Args:
        net_profit: PAT in ₹ Crore.
        equity_capital: Paid-up share capital in ₹ Crore.
        reserves: Reserves & surplus in ₹ Crore. May be None for some rows.

    Returns:
        ROE as a percentage, or None if total equity is zero/negative/null.

    Note:
        The source roe_percentage field in companies.xlsx appears to store
        ROE as a decimal ratio for some companies (e.g. TCS = 0.52 instead
        of the correct ~51%). Always use the computed value for analytics;
        source value is for display only.
    """
    if net_profit is None or equity_capital is None:
        return None
    total_equity = equity_capital + (reserves or 0.0)
    if total_equity <= 0:
        return None
    return round(net_profit / total_equity * 100, 4)


# ---------------------------------------------------------------------------
# Return on Capital Employed (ROCE)
# ---------------------------------------------------------------------------
def return_on_capital_employed(
    operating_profit: Optional[float],
    depreciation: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
    company_id: str = "",
) -> Optional[float]:
    """Compute ROCE: EBIT / (equity + reserves + borrowings) * 100.

    EBIT = operating_profit - depreciation.
    Capital Employed = equity_capital + reserves + borrowings.

    For Financial-sector companies, the absolute threshold benchmark
    (>15% = good) does not apply; sector-relative benchmarks are used
    instead. The formula itself is the same.

    Args:
        operating_profit: EBITDA in ₹ Crore.
        depreciation: D&A in ₹ Crore. May be None (treated as 0).
        equity_capital: Paid-up share capital in ₹ Crore.
        reserves: Reserves & surplus in ₹ Crore. May be None.
        borrowings: Total debt in ₹ Crore. May be None (treated as 0).
        company_id: NSE ticker — used to identify Financial-sector companies.

    Returns:
        ROCE as a percentage, or None if capital employed is zero/negative.
    """
    if operating_profit is None or equity_capital is None:
        return None

    ebit = operating_profit - (depreciation or 0.0)
    total_equity = equity_capital + (reserves or 0.0)
    capital_employed = total_equity + (borrowings or 0.0)

    if capital_employed <= 0:
        return None

    return round(ebit / capital_employed * 100, 4)


def roce_uses_sector_benchmark(company_id: str) -> bool:
    """Return True if this company's ROCE should be evaluated against
    sector-relative benchmarks rather than the absolute >15% threshold.
    """
    return is_financial(company_id)


# ---------------------------------------------------------------------------
# Return on Assets (ROA)
# ---------------------------------------------------------------------------
def return_on_assets(
    net_profit: Optional[float],
    total_assets: Optional[float],
) -> Optional[float]:
    """Compute Return on Assets: net_profit / total_assets * 100.

    Args:
        net_profit: PAT in ₹ Crore. Negative values are allowed.
        total_assets: Total asset base in ₹ Crore. Must be > 0.

    Returns:
        ROA as a percentage, or None if total_assets is zero/null.
    """
    if net_profit is None or total_assets is None:
        return None
    if total_assets == 0:
        return None
    return round(net_profit / total_assets * 100, 4)


# ---------------------------------------------------------------------------
# Batch computation helper
# ---------------------------------------------------------------------------
def compute_profitability_ratios(row: dict) -> dict:
    """Compute all Day 8 profitability ratios for a single company-year row.

    Args:
        row: Dictionary with keys matching the joined profitandloss +
             balancesheet column names, plus 'company_id'.

    Returns:
        Dictionary with computed ratio values. None where computation
        was not possible due to missing/invalid inputs.
    """
    company_id = row.get("company_id", "")

    npm = net_profit_margin(
        row.get("net_profit"),
        row.get("sales"),
    )
    opm = operating_profit_margin(
        row.get("operating_profit"),
        row.get("sales"),
    )
    _, opm_diff = opm_cross_check(opm, row.get("opm_percentage"))

    roe = return_on_equity(
        row.get("net_profit"),
        row.get("equity_capital"),
        row.get("reserves"),
    )
    roce = return_on_capital_employed(
        row.get("operating_profit"),
        row.get("depreciation"),
        row.get("equity_capital"),
        row.get("reserves"),
        row.get("borrowings"),
        company_id=company_id,
    )
    roa = return_on_assets(
        row.get("net_profit"),
        row.get("total_assets"),
    )

    return {
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "opm_source_diff": opm_diff,
        "return_on_equity_pct": roe,
        "return_on_capital_pct": roce,
        "roce_uses_sector_benchmark": roce_uses_sector_benchmark(company_id),
        "return_on_assets_pct": roa,
    }


# ---------------------------------------------------------------------------
# Day 9 — Leverage & Efficiency Ratios
# ---------------------------------------------------------------------------

def debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    company_id: str = "",
) -> tuple:
    """Compute Debt-to-Equity ratio: borrowings / (equity_capital + reserves).

    Args:
        borrowings: Total debt in ₹ Crore. None treated as 0 (debt-free).
        equity_capital: Paid-up share capital in ₹ Crore.
        reserves: Reserves & surplus in ₹ Crore. None treated as 0.
        company_id: NSE ticker — used for high-leverage flag check.

    Returns:
        Tuple of (de_ratio: float, high_leverage_flag: bool).
        de_ratio = 0.0 for debt-free companies (borrowings = 0).
        high_leverage_flag = True if D/E > 5 AND company is NOT in
        Financials sector (per spec: high leverage is structurally
        normal for banks/NBFCs).
    """
    if equity_capital is None:
        return None, False

    total_equity = equity_capital + (reserves or 0.0)
    if total_equity <= 0:
        return None, False

    total_borrowings = borrowings or 0.0
    de_ratio = round(total_borrowings / total_equity, 4)

    high_leverage_flag = (de_ratio > 5.0) and not is_financial(company_id)

    return de_ratio, high_leverage_flag


def interest_coverage_ratio(
    operating_profit: Optional[float],
    other_income: Optional[float],
    interest: Optional[float],
) -> tuple:
    """Compute Interest Coverage Ratio: (op_profit + other_income) / interest.

    Args:
        operating_profit: EBITDA in ₹ Crore.
        other_income: Non-operating income in ₹ Crore. None treated as 0.
        interest: Finance costs in ₹ Crore. 0 or None = debt-free.

    Returns:
        Tuple of (icr: float | None, icr_label: str).
        Returns (None, 'Debt Free') when interest is 0 or None.
        Returns (None, 'N/A') when operating_profit is None.
        icr_label = 'At Risk' when ICR < 1.5 (per spec warning flag).
    """
    if operating_profit is None:
        return None, "N/A"

    if not interest or interest == 0:
        return None, "Debt Free"

    icr = round((operating_profit + (other_income or 0.0)) / interest, 4)
    label = "At Risk" if icr < 1.5 else "OK"

    return icr, label


def net_debt(
    borrowings: Optional[float],
    investments: Optional[float],
) -> Optional[float]:
    """Compute Net Debt: borrowings - investments.

    investments is used as a liquid asset proxy per the spec.
    Negative result means the company is net-cash positive.

    Args:
        borrowings: Total debt in ₹ Crore. None treated as 0.
        investments: Long-term investments in ₹ Crore. None treated as 0.

    Returns:
        Net debt in ₹ Crore. Can be negative (net cash position).
    """
    return round((borrowings or 0.0) - (investments or 0.0), 4)


def asset_turnover(
    sales: Optional[float],
    total_assets: Optional[float],
) -> Optional[float]:
    """Compute Asset Turnover: sales / total_assets.

    Args:
        sales: Net revenue in ₹ Crore.
        total_assets: Total asset base in ₹ Crore. Must be > 0.

    Returns:
        Asset turnover ratio (times), or None if total_assets is 0/null.
    """
    if sales is None or total_assets is None:
        return None
    if total_assets == 0:
        return None
    return round(sales / total_assets, 4)


def compute_leverage_efficiency_ratios(row: dict) -> dict:
    """Compute all Day 9 leverage and efficiency ratios for a single row.

    Args:
        row: Dictionary with keys matching joined profitandloss +
             balancesheet column names, plus 'company_id'.

    Returns:
        Dictionary with computed ratio values.
    """
    company_id = row.get("company_id", "")

    de_ratio, high_leverage_flag = debt_to_equity(
        row.get("borrowings"),
        row.get("equity_capital"),
        row.get("reserves"),
        company_id=company_id,
    )

    icr, icr_label = interest_coverage_ratio(
        row.get("operating_profit"),
        row.get("other_income"),
        row.get("interest"),
    )

    nd = net_debt(
        row.get("borrowings"),
        row.get("investments"),
    )

    at = asset_turnover(
        row.get("sales"),
        row.get("total_assets"),
    )

    return {
        "debt_to_equity": de_ratio,
        "high_leverage_flag": high_leverage_flag,
        "interest_coverage": icr,
        "icr_label": icr_label,
        "net_debt_cr": nd,
        "asset_turnover": at,
    }
