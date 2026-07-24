"""
Day 30 — src/nlp/pros_cons_generator.py  (REAL DATA VERSION)

Primary source: `financial_ratios` table (real, computed in Sprint 2) —
covers 90 of 92 companies, multiple years each. Rules fire on the latest
year's values plus a margin trend vs. the prior year.

Fallback: for the 2 companies absent from financial_ratios (ATGL, SBIN),
use `companies.roe_percentage` / `roce_percentage` only, with a note that
data is limited.

Enrichment: for the 4 companies that have real analyst-reported text in
`prosandcons` (HDFCBANK, INFY, SBILIFE, TCS), that genuine reported text is
appended as-is (it's the user's own licensed data, not third-party
copyrighted material) alongside the rule-generated bullets.

Output: output/pros_cons_generated.csv
Columns: company_id, company_name, sector, Pros, Cons, Data_Source
  Data_Source in {"financial_ratios", "financial_ratios+reported", "limited (companies table only)"}

Guarantee (exit criteria): every one of the 92 companies gets >=1 pro
and >=1 con.
"""
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"
OUTPUT_PATH = "output/pros_cons_generated.csv"


def latest_two_years(g: pd.DataFrame):
    g = g.copy()
    g["year_dt"] = pd.to_datetime(g["year"], format="%b %Y", errors="coerce")
    g = g.sort_values("year_dt")
    latest = g.iloc[-1]
    prev = g.iloc[-2] if len(g) >= 2 else None
    return latest, prev


def rules_from_ratios(latest, prev):
    pros, cons = [], []

    if pd.notna(latest.get("revenue_cagr_5yr")):
        v = latest["revenue_cagr_5yr"]
        if v >= 12:
            pros.append(f"Strong 5-year revenue CAGR of {v:.1f}%")
        elif v < 3:
            cons.append(f"Weak 5-year revenue CAGR of {v:.1f}%")

    if pd.notna(latest.get("pat_cagr_5yr")):
        v = latest["pat_cagr_5yr"]
        if v >= 15:
            pros.append(f"Strong 5-year profit (PAT) CAGR of {v:.1f}%")
        elif v < 0:
            cons.append(f"Declining 5-year profit CAGR of {v:.1f}%")

    if pd.notna(latest.get("return_on_equity_pct")):
        v = latest["return_on_equity_pct"]
        if v >= 18:
            pros.append(f"High return on equity of {v:.1f}%")
        elif v < 8:
            cons.append(f"Low return on equity of {v:.1f}%")

    if pd.notna(latest.get("debt_to_equity")):
        v = latest["debt_to_equity"]
        if v > 1.5:
            cons.append(f"High leverage: debt-to-equity of {v:.2f}")
        elif v < 0.3:
            pros.append(f"Low leverage: debt-to-equity of {v:.2f}")

    if pd.notna(latest.get("interest_coverage")):
        v = latest["interest_coverage"]
        if v < 2:
            cons.append(f"Weak interest coverage of {v:.1f}x")
        elif v > 8:
            pros.append(f"Strong interest coverage of {v:.1f}x")

    if pd.notna(latest.get("dividend_payout_ratio_pct")):
        v = latest["dividend_payout_ratio_pct"]
        if v >= 40:
            pros.append(f"Healthy dividend payout ratio of {v:.1f}%")

    if prev is not None and pd.notna(latest.get("operating_profit_margin_pct")) and pd.notna(prev.get("operating_profit_margin_pct")):
        m1, m2 = prev["operating_profit_margin_pct"], latest["operating_profit_margin_pct"]
        if m2 - m1 >= 2:
            pros.append(f"Operating margin expanded from {m1:.1f}% to {m2:.1f}%")
        elif m1 - m2 >= 2:
            cons.append(f"Operating margin compressed from {m1:.1f}% to {m2:.1f}%")

    if pd.notna(latest.get("free_cash_flow_cr")):
        v = latest["free_cash_flow_cr"]
        if v < 0:
            cons.append("Negative free cash flow in the latest reported year")

    return pros, cons


def main():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    comp_ratios = pd.read_sql("SELECT id, roe_percentage, roce_percentage FROM companies", conn)
    pc_real = pd.read_sql("SELECT company_id, pros, cons FROM prosandcons", conn)
    conn.close()

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    name_map = dict(zip(companies["id"], companies["company_name"]))
    fallback_map = comp_ratios.set_index("id")[["roe_percentage", "roce_percentage"]].to_dict("index")

    # Aggregate real reported pros/cons text per company (dedup, join)
    real_pros = pc_real.dropna(subset=["pros"]).groupby("company_id")["pros"].apply(
        lambda s: list(dict.fromkeys(s.tolist()))
    ).to_dict()
    real_cons = pc_real.dropna(subset=["cons"]).groupby("company_id")["cons"].apply(
        lambda s: list(dict.fromkeys(s.tolist()))
    ).to_dict()

    rows = []
    fr_companies = set(fr["company_id"].unique())

    for _, comp in companies.iterrows():
        cid = comp["id"]
        pros, cons = [], []
        source = "financial_ratios"

        if cid in fr_companies:
            g = fr[fr["company_id"] == cid]
            latest, prev = latest_two_years(g)
            pros, cons = rules_from_ratios(latest, prev)
        else:
            source = "limited (companies table only)"
            fb = fallback_map.get(cid, {})
            roe = fb.get("roe_percentage")
            roce = fb.get("roce_percentage")
            if roe is not None and pd.notna(roe):
                if roe >= 18:
                    pros.append(f"High return on equity of {roe:.1f}%")
                elif roe < 8:
                    cons.append(f"Low return on equity of {roe:.1f}%")
            if roce is not None and pd.notna(roce):
                if roce >= 18:
                    pros.append(f"High return on capital employed of {roce:.1f}%")
                elif roce < 8:
                    cons.append(f"Low return on capital employed of {roce:.1f}%")

        # Merge in genuinely reported pros/cons where they exist
        if cid in real_pros:
            pros.extend(real_pros[cid])
            source = source + "+reported" if "reported" not in source else source
        if cid in real_cons:
            cons.extend(real_cons[cid])
            source = source + "+reported" if "reported" not in source else source

        # Guarantee (exit criteria): at least one pro and one con
        if not pros:
            pros.append("No standout strengths identified from available data")
        if not cons:
            cons.append("No major red flags identified from available data")

        rows.append({
            "company_id": cid,
            "company_name": name_map.get(cid, cid),
            "sector": sector_map.get(cid, "Unknown"),
            "Pros": "; ".join(pros),
            "Cons": "; ".join(cons),
            "Data_Source": source,
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_PATH, index=False)

    empty_pros = out["Pros"].str.len().eq(0).sum()
    empty_cons = out["Cons"].str.len().eq(0).sum()
    print(f"Wrote {OUTPUT_PATH} with {len(out)} rows (target: 92)")
    print(f"Rows with empty Pros: {empty_pros}, empty Cons: {empty_cons}")
    print(out["Data_Source"].value_counts())
    return out


if __name__ == "__main__":
    df = main()
    pd.set_option("display.max_colwidth", 50)
    print(df.head(10).to_string(index=False))
