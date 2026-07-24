"""Unit tests for src/analytics/cashflow_kpis.py — Day 11 cash flow KPIs.

Covers: FCF, CFO Quality Score, CapEx Intensity, FCF Conversion Rate,
and Capital Allocation 8-pattern classifier.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from cashflow_kpis import (  # noqa: E402
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    capital_allocation_pattern,
    CFO_QUALITY_HIGH,
    CFO_QUALITY_MODERATE,
    CFO_QUALITY_ACCRUAL_RISK,
    CAPEX_ASSET_LIGHT,
    CAPEX_MODERATE,
    CAPEX_CAPITAL_INTENSIVE,
)


# ---------------------------------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------------------------------
def test_fcf_normal_positive():
    assert free_cash_flow(1000, -400) == 600.0


def test_fcf_negative_allowed():
    """Negative FCF is valid — company spending more than it earns."""
    assert free_cash_flow(200, -500) == -300.0


def test_fcf_none_inputs():
    assert free_cash_flow(None, -400) is None
    assert free_cash_flow(1000, None) is None


# ---------------------------------------------------------------------------
# CFO Quality Score
# ---------------------------------------------------------------------------
def test_cfo_quality_high():
    """CFO/PAT > 1.0 → High Quality."""
    score, label = cfo_quality_score([1200, 1100, 1000], [1000, 900, 800])
    assert label == CFO_QUALITY_HIGH
    assert score > 1.0


def test_cfo_quality_moderate():
    """CFO/PAT between 0.5 and 1.0 → Moderate."""
    score, label = cfo_quality_score([700, 600], [1000, 1000])
    assert label == CFO_QUALITY_MODERATE


def test_cfo_quality_accrual_risk():
    """CFO/PAT < 0.5 → Accrual Risk."""
    score, label = cfo_quality_score([200], [1000])
    assert label == CFO_QUALITY_ACCRUAL_RISK


def test_cfo_quality_zero_pat_skipped():
    """Zero PAT rows should be skipped, not cause division by zero."""
    score, label = cfo_quality_score([1000, 500], [0, 1000])
    assert score is not None
    assert label == CFO_QUALITY_MODERATE


def test_cfo_quality_all_invalid():
    """All zero PAT → score is None."""
    score, label = cfo_quality_score([1000], [0])
    assert score is None
    assert label == "N/A"


# ---------------------------------------------------------------------------
# CapEx Intensity
# ---------------------------------------------------------------------------
def test_capex_asset_light():
    """< 3% → Asset Light (typical for IT companies)."""
    intensity, label = capex_intensity(-200, 10000)
    assert label == CAPEX_ASSET_LIGHT
    assert intensity == 2.0


def test_capex_moderate():
    intensity, label = capex_intensity(-500, 10000)
    assert label == CAPEX_MODERATE
    assert intensity == 5.0


def test_capex_capital_intensive():
    """Top 8% → Capital Intensive (typical for steel/power)."""
    intensity, label = capex_intensity(-1000, 10000)
    assert label == CAPEX_CAPITAL_INTENSIVE
    assert intensity == 10.0


def test_capex_zero_sales_returns_none():
    intensity, label = capex_intensity(-500, 0)
    assert intensity is None
    assert label == "N/A"


# ---------------------------------------------------------------------------
# FCF Conversion Rate
# ---------------------------------------------------------------------------
def test_fcf_conversion_normal():
    result = fcf_conversion_rate(600, 1000)
    assert result == 60.0


def test_fcf_conversion_zero_operating_profit():
    assert fcf_conversion_rate(600, 0) is None


def test_fcf_conversion_none_inputs():
    assert fcf_conversion_rate(None, 1000) is None


# ---------------------------------------------------------------------------
# Capital Allocation Pattern Classifier
# ---------------------------------------------------------------------------
def test_pattern_reinvestor():
    """(+,-,-) = Reinvestor — ops positive, investing and financing negative."""
    _, _, _, key, label = capital_allocation_pattern(1000, -500, -200)
    assert key == "(+,-,-)"
    assert label == "Reinvestor"


def test_pattern_distress_signal():
    """(-,+,+) = Distress Signal — negative ops, selling assets, raising debt."""
    _, _, _, key, label = capital_allocation_pattern(-500, 200, 300)
    assert key == "(-,+,+)"
    assert label == "Distress Signal"


def test_pattern_growth_funded_by_debt():
    """(-,-,+) = Growth Funded by Debt."""
    _, _, _, key, label = capital_allocation_pattern(-500, -300, 800)
    assert key == "(-,-,+)"
    assert label == "Growth Funded by Debt"


def test_pattern_none_input():
    """None input → Unknown pattern."""
    _, _, _, key, label = capital_allocation_pattern(None, -500, -200)
    assert key == "N/A"
    assert label == "Unknown"


def test_pattern_cash_accumulator():
    """(+,+,+) = Cash Accumulator."""
    _, _, _, key, label = capital_allocation_pattern(500, 200, 300)
    assert key == "(+,+,+)"
    assert label == "Cash Accumulator"
