"""Unit tests for src/analytics/ratios.py — Day 8 profitability ratios.

Per DAD-PROJ-001 Sprint 2, Day 8: 8 unit tests covering normal cases,
zero denominator (None), negative equity (None), and OPM cross-check.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from ratios import (  # noqa: E402
    net_profit_margin,
    operating_profit_margin,
    opm_cross_check,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    load_financial_sector_ids,
    roce_uses_sector_benchmark,
)


# ---------------------------------------------------------------------------
# Net Profit Margin
# ---------------------------------------------------------------------------
def test_npm_normal_case():
    """NPM = net_profit / sales * 100."""
    assert net_profit_margin(100, 500) == 20.0


def test_npm_zero_sales_returns_none():
    """NPM must return None when sales = 0 (DQ-06 scenario)."""
    assert net_profit_margin(100, 0) is None


def test_npm_negative_profit_allowed():
    """NPM can be negative (loss-making company)."""
    result = net_profit_margin(-50, 500)
    assert result == -10.0


def test_npm_none_inputs():
    """NPM returns None if either input is None."""
    assert net_profit_margin(None, 500) is None
    assert net_profit_margin(100, None) is None


# ---------------------------------------------------------------------------
# Operating Profit Margin & Cross-Check
# ---------------------------------------------------------------------------
def test_opm_normal_case():
    """OPM = operating_profit / sales * 100."""
    assert operating_profit_margin(150, 500) == 30.0


def test_opm_zero_sales_returns_none():
    """OPM must return None when sales = 0."""
    assert operating_profit_margin(150, 0) is None


def test_opm_cross_check_within_tolerance():
    """Cross-check passes when diff <= 1%."""
    within, diff = opm_cross_check(30.0, 30.5)
    assert within is True
    assert diff == 0.5


def test_opm_cross_check_exceeds_tolerance():
    """Cross-check fails when diff > 1% — should be flagged for logging."""
    within, diff = opm_cross_check(30.0, 32.5)
    assert within is False
    assert diff == 2.5


def test_opm_cross_check_none_inputs():
    """Cross-check returns (True, None) when either value is None."""
    within, diff = opm_cross_check(None, 30.0)
    assert within is True
    assert diff is None


# ---------------------------------------------------------------------------
# Return on Equity (ROE)
# ---------------------------------------------------------------------------
def test_roe_normal_case():
    """ROE = net_profit / (equity + reserves) * 100."""
    result = return_on_equity(100, 200, 300)
    assert result == round(100 / 500 * 100, 4)


def test_roe_negative_equity_returns_none():
    """ROE must return None when equity + reserves <= 0."""
    assert return_on_equity(100, 200, -300) is None


def test_roe_zero_equity_returns_none():
    """ROE must return None when equity + reserves == 0."""
    assert return_on_equity(100, 0, 0) is None


def test_roe_none_reserves_treated_as_zero():
    """ROE should work when reserves is None (treated as 0)."""
    result = return_on_equity(100, 500, None)
    assert result == 20.0


def test_roe_tcs_sanity_check():
    """TCS FY2024: net_profit=46099, equity=362, reserves=90127.
    Expected ROE ≈ 50.94% (NOT the 0.52 anomaly in source data).
    """
    result = return_on_equity(46099, 362, 90127)
    assert result is not None
    assert 50.0 < result < 52.0


# ---------------------------------------------------------------------------
# Return on Capital Employed (ROCE)
# ---------------------------------------------------------------------------
def test_roce_normal_case():
    """ROCE = EBIT / capital_employed * 100."""
    # EBIT = 150 - 20 = 130; Capital = 200 + 300 + 100 = 600
    result = return_on_capital_employed(150, 20, 200, 300, 100)
    assert result == round(130 / 600 * 100, 4)


def test_roce_zero_capital_returns_none():
    """ROCE must return None when capital employed is zero."""
    assert return_on_capital_employed(150, 20, 0, 0, 0) is None


def test_roce_none_borrowings_treated_as_zero():
    """ROCE should work when borrowings is None (debt-free company)."""
    result = return_on_capital_employed(150, 20, 200, 300, None)
    assert result is not None
    assert result == round(130 / 500 * 100, 4)


def test_roce_financial_sector_uses_benchmark_flag():
    """Financial sector companies should return True for sector benchmark flag."""
    load_financial_sector_ids({"HDFCBANK", "ICICIBANK", "SBIN"})
    assert roce_uses_sector_benchmark("HDFCBANK") is True
    assert roce_uses_sector_benchmark("TCS") is False


# ---------------------------------------------------------------------------
# Return on Assets (ROA)
# ---------------------------------------------------------------------------
def test_roa_normal_case():
    """ROA = net_profit / total_assets * 100."""
    assert return_on_assets(100, 1000) == 10.0


def test_roa_zero_assets_returns_none():
    """ROA must return None when total_assets = 0."""
    assert return_on_assets(100, 0) is None


def test_roa_none_inputs():
    """ROA returns None if either input is None."""
    assert return_on_assets(None, 1000) is None
    assert return_on_assets(100, None) is None


# ---------------------------------------------------------------------------
# Day 9 — Leverage & Efficiency Ratios
# ---------------------------------------------------------------------------
from ratios import (  # noqa: E402
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    asset_turnover,
)


def test_de_normal_case():
    """D/E = borrowings / (equity + reserves)."""
    ratio, flag = debt_to_equity(500, 200, 300)
    assert ratio == 1.0
    assert flag is False


def test_de_debt_free_returns_zero():
    """D/E must return 0.0 when borrowings = 0 (debt-free company)."""
    ratio, flag = debt_to_equity(0, 200, 300)
    assert ratio == 0.0
    assert flag is False


def test_de_none_borrowings_treated_as_zero():
    """D/E should treat None borrowings as 0 (debt-free)."""
    ratio, flag = debt_to_equity(None, 200, 300)
    assert ratio == 0.0
    assert flag is False


def test_de_high_leverage_flag_non_financial():
    """D/E > 5 for non-financial company should set high_leverage_flag=True."""
    load_financial_sector_ids({"HDFCBANK"})
    ratio, flag = debt_to_equity(3000, 200, 300)
    assert ratio > 5
    assert flag is True


def test_de_high_leverage_flag_suppressed_for_financials():
    """D/E > 5 for financial company should NOT set high_leverage_flag."""
    load_financial_sector_ids({"HDFCBANK"})
    ratio, flag = debt_to_equity(3000, 200, 300, company_id="HDFCBANK")
    assert ratio > 5
    assert flag is False


def test_icr_interest_zero_returns_debt_free():
    """ICR must return (None, 'Debt Free') when interest = 0."""
    icr, label = interest_coverage_ratio(1000, 100, 0)
    assert icr is None
    assert label == "Debt Free"


def test_icr_interest_none_returns_debt_free():
    """ICR must return (None, 'Debt Free') when interest = None."""
    icr, label = interest_coverage_ratio(1000, 100, None)
    assert icr is None
    assert label == "Debt Free"


def test_icr_normal_case():
    """ICR = (op_profit + other_income) / interest."""
    icr, label = interest_coverage_ratio(1000, 200, 400)
    assert icr == 3.0
    assert label == "OK"


def test_icr_at_risk_flag():
    """ICR < 1.5 should return 'At Risk' label."""
    icr, label = interest_coverage_ratio(100, 0, 200)
    assert icr == 0.5
    assert label == "At Risk"


def test_net_debt_positive():
    """Net debt = borrowings - investments."""
    assert net_debt(1000, 200) == 800.0


def test_net_debt_negative_means_net_cash():
    """Negative net debt = company holds more cash/investments than debt."""
    assert net_debt(200, 1000) == -800.0


def test_net_debt_none_treated_as_zero():
    """None values treated as 0."""
    assert net_debt(None, None) == 0.0


def test_asset_turnover_normal_case():
    """Asset turnover = sales / total_assets."""
    assert asset_turnover(1000, 500) == 2.0


def test_asset_turnover_zero_assets_returns_none():
    """Asset turnover must return None when total_assets = 0."""
    assert asset_turnover(1000, 0) is None


def test_asset_turnover_none_inputs():
    """Asset turnover returns None if either input is None."""
    assert asset_turnover(None, 500) is None
    assert asset_turnover(1000, None) is None
