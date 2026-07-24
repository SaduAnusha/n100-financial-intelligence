"""
Day 29 — src/nlp/parser.py  (REAL DATA VERSION)

The `analysis` table in nifty100.db stores period-based growth figures as
free text, e.g. compounded_sales_growth = "10 Years:     21%". Each company
has up to 4 rows (10/5/3 Years + TTM). This script parses that text into a
clean, structured long-format table.

NOTE ON COVERAGE: the source analysis.xlsx only contains data for 4 of the
92 companies (HDFCBANK, INFY, SBILIFE, TCS) — the header literally says
"20 records" total, not per-company. This is a real limitation of the
source file, not a parsing bug. output/analysis_parsed.csv will therefore
only have rows for those 4 tickers; this is expected and documented in
output/parser_coverage_note.txt.

Output: output/analysis_parsed.csv
Columns: company_id, period, sales_growth_pct, profit_growth_pct,
         stock_price_cagr_pct, roe_pct
"""
import re
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"
OUTPUT_PATH = "output/analysis_parsed.csv"
COVERAGE_NOTE_PATH = "output/parser_coverage_note.txt"

PERIOD_VALUE_RE = re.compile(r"((?:\d+\s*Years?)|TTM)\s*:\s*(-?\d+\.?\d*)\s*%?", re.IGNORECASE)


def parse_period_value(text):
    """'10 Years:     21%' -> ('10 Years', 21.0). Returns (None, None) if unparseable."""
    if text is None:
        return None, None
    m = PERIOD_VALUE_RE.search(str(text).strip())
    if not m:
        return None, None
    period_raw = m.group(1).strip()
    value = float(m.group(2))
    # Normalise whitespace: "10   Years" -> "10 Years"
    period = "TTM" if period_raw.upper() == "TTM" else re.sub(r"\s+", " ", period_raw)
    return period, value


def parse_analysis(db_path: str = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM analysis", conn)
    conn.close()

    records = []
    failures = []
    for _, row in df.iterrows():
        period_s, sales = parse_period_value(row["compounded_sales_growth"])
        period_p, profit = parse_period_value(row["compounded_profit_growth"])
        period_c, price_cagr = parse_period_value(row["stock_price_cagr"])
        period_r, roe = parse_period_value(row["roe"])

        # The 4 fields should share the same period per row; use whichever parsed
        period = period_s or period_p or period_c or period_r
        if period is None:
            failures.append(row.to_dict())
            continue

        records.append({
            "company_id": row["company_id"],
            "period": period,
            "sales_growth_pct": sales,
            "profit_growth_pct": profit,
            "stock_price_cagr_pct": price_cagr,
            "roe_pct": roe,
        })

    out = pd.DataFrame(records)
    if failures:
        print(f"WARNING: {len(failures)} rows failed to parse:")
        for f in failures:
            print(" ", f)

    return out


if __name__ == "__main__":
    parsed = parse_analysis()
    parsed.to_csv(OUTPUT_PATH, index=False)

    covered_companies = sorted(parsed["company_id"].unique().tolist())
    with open(COVERAGE_NOTE_PATH, "w") as f:
        f.write(
            "SCOPE NOTE: The source data/raw/analysis.xlsx file only contains "
            "records for the following companies (confirmed against the raw file "
            "header, which states the total record count, not per-company):\n"
            f"{covered_companies}\n\n"
            "All other Nifty100 companies have no rows in the `analysis` table "
            "in nifty100.db. This is a source data gap from Sprint 1 ETL, not a "
            "parser bug -- there is nothing to parse for the other companies.\n"
        )

    print(f"Wrote {OUTPUT_PATH} with {len(parsed)} rows, covering {len(covered_companies)} companies: {covered_companies}")
    print(parsed.to_string(index=False))
