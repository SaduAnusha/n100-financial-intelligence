"""Normalisation functions for the N100 Financial Intelligence Platform ETL pipeline.

Handles two recurring data-quality problems found across the 7 core Excel
datasets:
  1. Inconsistent financial-year labels (e.g. "Mar-23", "Mar 2014", "2024",
     "FY23", "Dec-22", "2024.5").
  2. Inconsistent NSE ticker casing/whitespace (e.g. "tcs", " TCS ").

Both functions are pure (no I/O) so they are easy to unit test in isolation.
"""

import re
from typing import Optional

# Maps recognised month names/abbreviations to their 2-digit numeric form.
_MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "sept": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

# Already-normalised "YYYY-MM" strings should pass through untouched.
_ALREADY_NORMALISED_RE = re.compile(r"^\d{4}-\d{2}$")

# "Mar-23", "Mar 2014", "Dec-22", "March-2023", "Jun 2013" (month + sep + year)
_MONTH_YEAR_RE = re.compile(
    r"^([A-Za-z]+)[\s\-]+(\d{2,4})$"
)

# "FY23", "FY2023"
_FY_PREFIX_RE = re.compile(r"^FY[\s\-]?(\d{2,4})$", re.IGNORECASE)

# Bare 4-digit year, e.g. "2024". Per spec: integer year -> assume March FY close.
_BARE_YEAR_RE = re.compile(r"^\d{4}$")

PARSE_ERROR = "PARSE_ERROR"


def _expand_2digit_year(yy: str) -> str:
    """Expand a 2-digit year to 4 digits.

    Uses a pivot at 50: 00-49 -> 2000-2049, 50-99 -> 1950-1999.
    All data in this project is post-2010, so this heuristic is safe.
    """
    yy_int = int(yy)
    if yy_int <= 49:
        return f"20{yy_int:02d}"
    return f"19{yy_int:02d}"


def normalize_year(raw_value) -> Optional[str]:
    """Standardise a raw financial-year label to 'YYYY-MM' format.

    Handles the formats documented in DAD-PROJ-001 Section 23 (ETL Edge
    Cases), including both "Mar-23" (hyphen, 2-digit year) and
    "Mar 2014" (space, 4-digit year) variants found in the real source
    files, plus bare years, FY-prefixed years, and already-normalised
    values.

    Args:
        raw_value: The raw year value from the source Excel file. May be
            a string, int, or float (pandas sometimes reads "2024.5" as
            a float when a column is mixed-type).

    Returns:
        A string in 'YYYY-MM' format, or None if the value could not be
        parsed (per DQ-07: CRITICAL — reject row, log raw value).
    """
    if raw_value is None:
        return None

    # Handle the real-world "2024.5" anomaly and other float years.
    if isinstance(raw_value, float):
        if raw_value.is_integer():
            raw_value = str(int(raw_value))
        else:
            # e.g. 2024.5 -- not a valid year/month encoding. Reject.
            return None

    text = str(raw_value).strip()
    if not text:
        return None

    # Already normalised: "2023-03"
    if _ALREADY_NORMALISED_RE.match(text):
        return text

    # Bare 4-digit year: "2023" -> assume March FY close per spec.
    if _BARE_YEAR_RE.match(text):
        return f"{text}-03"

    # "FY23" / "FY2023" -> March FY close.
    fy_match = _FY_PREFIX_RE.match(text)
    if fy_match:
        yy = fy_match.group(1)
        year = yy if len(yy) == 4 else _expand_2digit_year(yy)
        return f"{year}-03"

    # "Mar-23", "Mar 2014", "March-2023", "Dec-22", "Jun 2013", etc.
    my_match = _MONTH_YEAR_RE.match(text)
    if my_match:
        month_raw, year_raw = my_match.groups()
        month = _MONTH_MAP.get(month_raw.lower())
        if month is None:
            return None
        year = year_raw if len(year_raw) == 4 else _expand_2digit_year(year_raw)
        return f"{year}-{month}"

    # Nothing matched -> unparseable.
    return None


def normalize_ticker(raw_value) -> Optional[str]:
    """Standardise an NSE ticker / company_id value.

    Strips surrounding whitespace and uppercases the value. Preserves
    internal punctuation that is valid in real NSE tickers, such as the
    hyphen in "BAJAJ-AUTO" and the ampersand in "M&M".

    Args:
        raw_value: The raw company_id / ticker value from the source file.

    Returns:
        The normalised ticker string, or None if the value is missing,
        empty, or outside the valid length range (2-12 chars per DQ-08).
    """
    if raw_value is None:
        return None

    text = str(raw_value).strip().upper()
    if not text or text == "NAN":
        return None

    if not (2 <= len(text) <= 12):
        return None

    return text
