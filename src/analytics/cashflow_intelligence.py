"""
Day 31+32 — src/analytics/cashflow_intelligence.py (REAL DATA VERSION)

Reads db/nifty100.db (cashflow + balancesheet tables) and computes, per
company, using the latest reported year:
  - CFO_Quality = CFO / cash_from_operations comparison isn't needed here;
    we use financial_ratios.free_cash_flow_cr where available, else derive
    CFO/CapEx directly from cashflow+balancesheet.
  - CapEx intensity = CapEx / CFO
  - Capital allocation classification (Self-funded Expansion / Debt-funded
    Expansion / Deleveraging / Distress / Balanced)
  - Distress flag: negative CFO, or CFO fell >20% while borrowings rose >10%

Output: output/cashflow_intelligence.xlsx (Summary + History sheets)
        output/distress_alerts.csv
"""
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"
XLSX_OUT = "output/cashflow_intelligence.xlsx"
CSV_OUT = "output/distress_alerts.csv"


def classify_capital_allocation(cfo, cfi, cff):
    if pd.isna(cfo) or cfo <= 0:
        return "Distress"
    if cfi < 0 and cff < 0:
        return "Self-funded Expansion"
    if cfi < 0 and cff > 0:
        return "Debt/Equity-funded Expansion"
    if cfi >= 0 and cff < 0:
        return "Deleveraging"
    return "Balanced"


def main():
    conn = sqlite3.connect(DB_PATH)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    for df in (cf, bs):
        df["year_dt"] = pd.to_datetime(df["year"], format="%Y-%m", errors="coerce")

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    name_map = dict(zip(companies["id"], companies["company_name"]))

    merged = pd.merge(
        cf, bs[["company_id", "year", "equity_capital", "reserves", "borrowings", "other_liabilities"]],
        on=["company_id", "year"], how="left"
    )
    merged["equity_total"] = merged["equity_capital"].fillna(0) + merged["reserves"].fillna(0)

    rows = []
    skipped = []
    for cid, g in merged.groupby("company_id"):
        g = g.sort_values("year_dt").dropna(subset=["year_dt"])
        if len(g) < 2:
            skipped.append(cid)
            continue
        latest = g.iloc[-1]
        prev = g.iloc[-2]

        cfo = latest["operating_activity"]
        cfi = latest["investing_activity"]
        cff = latest["financing_activity"]
        net = latest["net_cash_flow"]
        capex = abs(cfi) if pd.notna(cfi) else None  # investing activity used as capex proxy

        capex_intensity = (capex / cfo) if (capex is not None and cfo not in (0, None) and pd.notna(cfo)) else None

        distress = False
        reasons = []
        if pd.notna(cfo) and cfo < 0:
            distress = True
            reasons.append("Negative CFO")
        if pd.notna(prev["operating_activity"]) and prev["operating_activity"] != 0 and pd.notna(latest["borrowings"]) and pd.notna(prev["borrowings"]) and prev["borrowings"] != 0:
            cfo_decline = (cfo - prev["operating_activity"]) / abs(prev["operating_activity"])
            borrow_growth = (latest["borrowings"] - prev["borrowings"]) / prev["borrowings"]
            if cfo_decline < -0.20 and borrow_growth > 0.10:
                distress = True
                reasons.append("CFO declined >20% while borrowings rose >10%")

        allocation = classify_capital_allocation(cfo, cfi, cff)

        rows.append({
            "company_id": cid,
            "company_name": name_map.get(cid, cid),
            "sector": sector_map.get(cid, "Unknown"),
            "latest_year": latest["year"],
            "CFO": cfo, "CFI": cfi, "CFF": cff, "NetCashFlow": net,
            "CapEx_proxy": capex,
            "CapEx_Intensity": round(capex_intensity, 2) if capex_intensity is not None else None,
            "Capital_Allocation": allocation,
            "Distress_Flag": distress,
            "Distress_Reasons": "; ".join(reasons) if reasons else "",
        })

    summary = pd.DataFrame(rows)

    with pd.ExcelWriter(XLSX_OUT, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        merged.drop(columns=["year_dt"]).to_excel(writer, sheet_name="History", index=False)

    distress = summary[summary["Distress_Flag"]]
    distress.to_csv(CSV_OUT, index=False)

    print(f"Wrote {XLSX_OUT} with {len(summary)} companies (skipped {len(skipped)}: {skipped})")
    print(f"Wrote {CSV_OUT} with {len(distress)} flagged companies")
    print(summary["Capital_Allocation"].value_counts())
    return summary


if __name__ == "__main__":
    main()
