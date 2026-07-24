"""Unit tests for src/etl/normaliser.py.

Per DAD-PROJ-001 Day 2 deliverable: 20+ test cases for normalize_year(),
15+ test cases for normalize_ticker().
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "etl"))

from normaliser import normalize_year, normalize_ticker  # noqa: E402


# ---------------------------------------------------------------------------
# normalize_year() — 20+ cases
# ---------------------------------------------------------------------------

def test_year_mar_hyphen_2digit():
    assert normalize_year("Mar-23") == "2023-03"


def test_year_mar_space_4digit():
    assert normalize_year("Mar 2014") == "2014-03"


def test_year_mar_space_no_extra():
    assert normalize_year("Mar 23") == "2023-03"


def test_year_full_month_name_hyphen():
    assert normalize_year("March-2023") == "2023-03"


def test_year_bare_integer():
    assert normalize_year("2023") == "2023-03"


def test_year_bare_int_type():
    assert normalize_year(2023) == "2023-03"


def test_year_fy_prefix_2digit():
    assert normalize_year("FY23") == "2023-03"


def test_year_fy_prefix_4digit():
    assert normalize_year("FY2023") == "2023-03"


def test_year_fy_lowercase():
    assert normalize_year("fy23") == "2023-03"


def test_year_dec_hyphen():
    assert normalize_year("Dec-22") == "2022-12"


def test_year_dec_space_4digit():
    assert normalize_year("Dec 2022") == "2022-12"


def test_year_jun_hyphen():
    assert normalize_year("Jun-23") == "2023-06"


def test_year_jun_space_4digit():
    assert normalize_year("Jun 2013") == "2013-06"


def test_year_sep_space_4digit():
    assert normalize_year("Sep 2014") == "2014-09"


def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"


def test_year_garbage_string():
    assert normalize_year("xyz") is None


def test_year_garbage_word():
    assert normalize_year("garbage") is None


def test_year_float_anomaly():
    # Real-world anomaly found in balancesheet.xlsx: "2024.5"
    assert normalize_year(2024.5) is None


def test_year_float_whole_number():
    # pandas may read a bare year as a float, e.g. 2023.0
    assert normalize_year(2023.0) == "2023-03"


def test_year_none_value():
    assert normalize_year(None) is None


def test_year_empty_string():
    assert normalize_year("") is None


def test_year_whitespace_only():
    assert normalize_year("   ") is None


def test_year_2digit_pivot_low():
    # 00-49 maps to 2000-2049
    assert normalize_year("Mar-05") == "2005-03"


def test_year_2digit_pivot_high():
    # 50-99 maps to 1950-1999
    assert normalize_year("Mar-95") == "1995-03"


def test_year_unknown_month():
    assert normalize_year("Xyz-23") is None


# ---------------------------------------------------------------------------
# normalize_ticker() — 15+ cases
# ---------------------------------------------------------------------------

def test_ticker_already_upper():
    assert normalize_ticker("TCS") == "TCS"


def test_ticker_lowercase():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_mixed_case():
    assert normalize_ticker("TcS") == "TCS"


def test_ticker_leading_whitespace():
    assert normalize_ticker("  TCS") == "TCS"


def test_ticker_trailing_whitespace():
    assert normalize_ticker("TCS  ") == "TCS"


def test_ticker_both_side_whitespace():
    assert normalize_ticker("  tcs  ") == "TCS"


def test_ticker_hyphenated():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"


def test_ticker_ampersand():
    assert normalize_ticker("m&m") == "M&M"


def test_ticker_ampersand_already_upper():
    assert normalize_ticker("M&M") == "M&M"


def test_ticker_none_value():
    assert normalize_ticker(None) is None


def test_ticker_empty_string():
    assert normalize_ticker("") is None


def test_ticker_whitespace_only():
    assert normalize_ticker("   ") is None


def test_ticker_too_short():
    # Below 2-char minimum per DQ-08
    assert normalize_ticker("A") is None


def test_ticker_too_long():
    # Above 12-char maximum per DQ-08
    assert normalize_ticker("THISISWAYTOOLONGATICKER") is None


def test_ticker_min_length_boundary():
    # Exactly 2 chars should pass
    assert normalize_ticker("ab") == "AB"


def test_ticker_max_length_boundary():
    # Exactly 12 chars should pass
    assert normalize_ticker("abcdefghijkl") == "ABCDEFGHIJKL"


def test_ticker_nan_string():
    # pandas sometimes stringifies a missing cell as "nan"
    assert normalize_ticker("nan") is None


def test_ticker_real_sample_adanigreen():
    assert normalize_ticker(" AdaniGreen ") == "ADANIGREEN"
