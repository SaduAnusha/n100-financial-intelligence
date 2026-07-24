"""
Day 35 — src/reports/portfolio_summary.py  (REAL DATA VERSION)

One page per company, alphabetical by ticker (company_id). Each page shows
company name, sector, and 6 KPIs with a trend arrow comparing the latest
reported year to the prior year:
  up arrow    -> metric improved (increased) vs prior year
  down arrow  -> metric declined vs prior year
  right arrow -> flat, within 2% of prior year's value

Output: reports/portfolio/portfolio_summary.pdf
"""
import sqlite3
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

DB_PATH = "db/nifty100.db"
OUT_PATH = "reports/portfolio/portfolio_summary.pdf"

styles = getSampleStyleSheet()
cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=10, leading=13)
header_cell_style = ParagraphStyle("header_cell", parent=styles["Normal"], fontSize=10, leading=13, textColor=colors.white, fontName="Helvetica-Bold")

TOP6_METRICS = [
    ("revenue_cagr_5yr", "Revenue CAGR (5yr)", "%"),
    ("pat_cagr_5yr", "Profit CAGR (5yr)", "%"),
    ("return_on_equity_pct", "Return on Equity", "%"),
    ("operating_profit_margin_pct", "Operating Margin", "%"),
    ("net_profit_margin_pct", "Net Margin", "%"),
    ("debt_to_equity", "Debt to Equity", ""),
]

UP, DOWN, FLAT = "\u2191", "\u2193", "\u2192"


def trend_arrow(latest_val, prev_val):
    if latest_val is None or prev_val is None or pd.isna(latest_val) or pd.isna(prev_val):
        return ""
    if prev_val == 0:
        return ""
    pct_change = (latest_val - prev_val) / abs(prev_val)
    if abs(pct_change) <= 0.02:
        return FLAT
    return UP if pct_change > 0 else DOWN


def fmt(v, suffix="", decimals=1):
    if v is None or pd.isna(v):
        return "N/A"
    return f"{v:.{decimals}f}{suffix}"


def wrap_row(cells, style=cell_style):
    return [Paragraph(str(c), style) for c in cells]


def main():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    comp_fallback = pd.read_sql("SELECT id, roe_percentage, roce_percentage FROM companies", conn)
    conn.close()

    fr["year_dt"] = pd.to_datetime(fr["year"], format="%b %Y", errors="coerce")
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    fallback_map = comp_fallback.set_index("id")[["roe_percentage", "roce_percentage"]].to_dict("index")
    fr_companies = set(fr["company_id"].unique())

    doc = SimpleDocTemplate(OUT_PATH, pagesize=A4,
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = []

    companies_sorted = companies.sort_values("id")  # alphabetical by ticker
    n = len(companies_sorted)

    for idx, (_, comp) in enumerate(companies_sorted.iterrows()):
        cid = comp["id"]
        name = comp["company_name"]
        sector = sector_map.get(cid, "Unknown")

        story.append(Paragraph(f"{name} ({cid})", styles["Title"]))
        story.append(Paragraph(f"Sector: {sector}", ParagraphStyle("sub", parent=styles["Normal"], textColor=colors.grey)))
        story.append(Spacer(1, 14))

        rows = [wrap_row(["Metric", "Latest Value", "Trend"], header_cell_style)]

        if cid in fr_companies:
            g = fr[fr["company_id"] == cid].sort_values("year_dt").dropna(subset=["year_dt"])
            latest = g.iloc[-1]
            prev = g.iloc[-2] if len(g) >= 2 else None
            for col, label, suffix in TOP6_METRICS:
                latest_val = latest.get(col)
                prev_val = prev.get(col) if prev is not None else None
                arrow = trend_arrow(latest_val, prev_val)
                rows.append(wrap_row([label, fmt(latest_val, suffix), arrow]))
        else:
            fb = fallback_map.get(cid, {})
            rows.append(wrap_row(["Return on Equity", fmt(fb.get("roe_percentage"), "%"), ""]))
            rows.append(wrap_row(["Return on Capital Employed", fmt(fb.get("roce_percentage"), "%"), ""]))
            rows.append(wrap_row(["Note", "Limited financial ratio history available", ""]))

        table = Table(rows, colWidths=[7 * cm, 6 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("FONTSIZE", (2, 1), (2, -1), 13),
        ]))
        story.append(table)

        if idx < n - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Wrote {OUT_PATH} — {n} pages (one per company, alphabetical by ticker)")


if __name__ == "__main__":
    main()
