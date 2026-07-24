"""
Day 34 — src/reports/sector_report.py  (REAL DATA VERSION)

Generates one PDF per broad_sector:
  - Sector summary: median of key KPIs across all companies in the sector
  - Table listing every company in the sector with 8 metrics each

NOTE: The real `sectors` table has 10 distinct broad_sector values, not 11
as the original spec assumed. This reflects the actual sector taxonomy
used in the source data (data/raw/sectors.xlsx), not a bug in this script.

Output: reports/sector/<sector>_report.pdf  (one per sector)
"""
import os
import re
import sqlite3
import pandas as pd

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

DB_PATH = "db/nifty100.db"
OUT_DIR = "reports/sector"
os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=7, leading=9)
header_cell_style = ParagraphStyle("header_cell", parent=styles["Normal"], fontSize=7, leading=9, textColor=colors.white, fontName="Helvetica-Bold")

METRICS = [
    ("revenue_cagr_5yr", "Rev CAGR 5yr", "%"),
    ("pat_cagr_5yr", "PAT CAGR 5yr", "%"),
    ("return_on_equity_pct", "ROE", "%"),
    ("debt_to_equity", "D/E", ""),
    ("interest_coverage", "Int. Cov.", "x"),
    ("operating_profit_margin_pct", "Op. Margin", "%"),
    ("net_profit_margin_pct", "Net Margin", "%"),
    ("dividend_payout_ratio_pct", "Div Payout", "%"),
]


def safe_filename(name):
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def fmt(v, suffix="", decimals=1):
    if v is None or pd.isna(v):
        return "N/A"
    return f"{v:.{decimals}f}{suffix}"


def wrap_row(cells, style=cell_style):
    return [Paragraph(str(c), style) for c in cells]


def main():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    conn.close()

    fr["year_dt"] = pd.to_datetime(fr["year"], format="%b %Y", errors="coerce")
    latest_fr = fr.sort_values("year_dt").groupby("company_id").tail(1)

    merged = sectors.merge(companies, left_on="company_id", right_on="id", how="left")
    merged = merged.merge(latest_fr, on="company_id", how="left")

    sector_names = sorted(merged["broad_sector"].dropna().unique().tolist())
    print(f"Generating {len(sector_names)} sector PDFs (real data has {len(sector_names)} sectors, not the assumed 11)")

    for sector in sector_names:
        g = merged[merged["broad_sector"] == sector].sort_values("company_name")
        out_path = os.path.join(OUT_DIR, f"{safe_filename(sector)}_report.pdf")

        doc = SimpleDocTemplate(out_path, pagesize=landscape(A4),
                                 topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                                 leftMargin=1.2 * cm, rightMargin=1.2 * cm)
        story = []
        story.append(Paragraph(f"{sector} — Sector Report", styles["Title"]))
        story.append(Paragraph(f"{len(g)} companies", ParagraphStyle("sub", parent=styles["Normal"], textColor=colors.grey)))
        story.append(Spacer(1, 10))

        # Median KPI summary
        story.append(Paragraph("Sector Median KPIs", styles["Heading2"]))
        median_row = [wrap_row([label for _, label, _ in METRICS], header_cell_style)]
        medians = []
        for col, label, suffix in METRICS:
            med = g[col].median() if col in g.columns else None
            medians.append(fmt(med, suffix))
        median_row.append(wrap_row(medians))
        median_table = Table(median_row, colWidths=[3.2 * cm] * len(METRICS))
        median_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(median_table)
        story.append(Spacer(1, 16))

        # Per-company table
        story.append(Paragraph("Companies in Sector", styles["Heading2"]))
        header = ["Company"] + [label for _, label, _ in METRICS]
        rows = [wrap_row(header, header_cell_style)]
        for _, row in g.iterrows():
            vals = [row["company_name"] or row["company_id"]]
            for col, _, suffix in METRICS:
                vals.append(fmt(row.get(col), suffix))
            rows.append(wrap_row(vals))

        col_widths = [4.5 * cm] + [3.0 * cm] * len(METRICS)
        company_table = Table(rows, colWidths=col_widths, repeatRows=1)
        company_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]))
        story.append(company_table)

        doc.build(story)
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  {sector}: {out_path} ({size_kb:.1f} KB, {len(g)} companies)")


if __name__ == "__main__":
    main()
