"""Unit tests for src/analytics/cagr.py — Day 10 CAGR engine.

Per DAD-PROJ-001 Sprint 2, Day 10: 10 unit tests covering all 6 edge
cases: normal CAGR, turnaround, decline-to-loss, both negative,
zero base, and insufficient data.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from cagr import (  # noqa: E402
    compute_cagr,
    compute_cagr_for_company,
    FLAG_NORMAL,
    FLAG_TURNAROUND,
    FLAG_DECLINE_TO_LOSS,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT,
)


# ---------------------------------------------------------------------------
# compute_cagr() — 6 edge case tests
# ---------------------------------------------------------------------------

def test_cagr_normal_case():
    """Normal CAGR: base=100, end=161, n=5 → approx 10%."""
    cagr, flag = compute_cagr(100, 161.05, 5)
    assert flag == FLAG_NORMAL
    assert cagr is not None
    assert 9.9 < cagr < 10.1


def test_cagr_turnaround():
    """Base negative, end positive → TURNAROUND flag, None value."""
    cagr, flag = compute_cagr(-100, 200, 5)
    assert cagr is None
    assert flag == FLAG_TURNAROUND


def test_cagr_decline_to_loss():
    """Base positive, end negative → DECLINE_TO_LOSS flag, None value."""
    cagr, flag = compute_cagr(200, -50, 5)
    assert cagr is None
    assert flag == FLAG_DECLINE_TO_LOSS


def test_cagr_both_negative():
    """Both values negative → BOTH_NEGATIVE flag, None value."""
    cagr, flag = compute_cagr(-100, -200, 5)
    assert cagr is None
    assert flag == FLAG_BOTH_NEGATIVE


def test_cagr_zero_base():
    """Base value = 0 → ZERO_BASE flag, None value."""
    cagr, flag = compute_cagr(0, 200, 5)
    assert cagr is None
    assert flag == FLAG_ZERO_BASE


def test_cagr_insufficient_none_input():
    """None input → INSUFFICIENT flag, None value."""
    cagr, flag = compute_cagr(None, 200, 5)
    assert cagr is None
    assert flag == FLAG_INSUFFICIENT


def test_cagr_high_growth():
    """High growth CAGR sanity check: 100 → 400 over 5 years ≈ 32%."""
    cagr, flag = compute_cagr(100, 400, 5)
    assert flag == FLAG_NORMAL
    assert 31.0 < cagr < 33.0


def test_cagr_negative_growth():
    """Declining company: 1000 → 500 over 5 years ≈ -12.9%."""
    cagr, flag = compute_cagr(1000, 500, 5)
    assert flag == FLAG_NORMAL
    assert cagr is not None
    assert cagr < 0


# ---------------------------------------------------------------------------
# compute_cagr_for_company() — insufficient data test
# ---------------------------------------------------------------------------

def test_cagr_insufficient_history():
    """Company with only 2 years of data → INSUFFICIENT for 3yr window."""
    df = pd.DataFrame({
        "company_id": ["TEST", "TEST"],
        "year": ["2022-03", "2023-03"],
        "sales": [100, 120],
    })
    result = compute_cagr_for_company(df, "TEST", "sales", "2023-03", windows=[3])
    assert result["sales_cagr_3yr"] is None
    assert result["sales_cagr_3yr_flag"] == FLAG_INSUFFICIENT


def test_cagr_sufficient_history():
    """Company with 4 years → can compute 3yr CAGR correctly."""
    df = pd.DataFrame({
        "company_id": ["TEST"] * 4,
        "year": ["2020-03", "2021-03", "2022-03", "2023-03"],
        "sales": [100, 110, 120, 133.1],
    })
    result = compute_cagr_for_company(df, "TEST", "sales", "2023-03", windows=[3])
    assert result["sales_cagr_3yr_flag"] == FLAG_NORMAL
    assert result["sales_cagr_3yr"] is not None
    assert 9.9 < result["sales_cagr_3yr"] < 10.1
