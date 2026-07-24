"""
Day 33+34 — src/reports/tearsheet.py  (REAL DATA VERSION)

Page 1: Header + KPI table (from financial_ratios, latest year) + summary
Page 2: Balance Sheet composition stacked bar (real balancesheet history) +
        Cash Flow waterfall (real cashflow, latest year) + Pros (green) +
        Cons (red) + Capital Allocation badge

Skips companies with fewer than 3 years of balance sheet history, logging
them to output/skipped_tearsheets.csv (exit criteria requirement).

Usage:
    python src/reports/tearsheet.py            # batch: all companies
    python src/reports/tearsheet.py TCS ONGC    # subset (testing)
"""
import os
import sys
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)

DB_PATH = "db/nifty100.db"
PROSCONS_PATH = "output/pros_cons_generated.csv"
CASHFLOW_PATH = "output/cashflow_intelligence.xlsx"
OUT_DIR = "reports/tearsheets"
CHART_TMP_DIR = "/tmp/tearsheet_charts_real"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CHART_TMP_DIR, exist_ok=True)

styles = getSampleStyleSheet()
cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10)
header_cell_style = ParagraphStyle("header_cell", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold")
pro_style = ParagraphStyle("pro", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#1a7a1a"))
con_style = ParagraphStyle("con", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#b02a2a"))


def wrap_row(cells, style=cell_style):
    return [Paragraph(str(c), style) for c in cells]


def fmt(v, suffix="", decimals=1):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.{decimals}f}{suffix}"


def make_balance_sheet_chart(bs_hist: pd.DataFrame, ticker: str) -> str:
    fig, ax = plt.subplots(figsize=(5.2, 3.0), dpi=150)
    years = bs_hist["year"].tolist()
    equity = bs_hist["equity_capital"].fillna(0) + bs_hist["reserves"].fillna(0)
    borrow = bs_hist["borrowings"].fillna(0)
    other = bs_hist["other_liabilities"].fillna(0)
    ax.bar(years, equity, label="Equity", color="#2E7D32")
    ax.bar(years, borrow, bottom=equity, label="Borrowings", color="#C62828")
    ax.bar(years, other, bottom=equity + borrow, label="Other Liabilities", color="#F9A825")
    ax.set_title("Balance Sheet Composition", fontsize=10)
    ax.set_ylabel("Rs. Cr", fontsize=8)
    ax.tick_params(labelsize=6, rotation=45)
    ax.legend(fontsize=6, loc="upper left")
    fig.tight_layout()
    path = os.path.join(CHART_TMP_DIR, f"{ticker}_bs.png")
    fig.savefig(path)
    plt.close(fig)
    return path


def make_cashflow_waterfall(cfo, cfi, cff, net, ticker: str) -> str:
    labels = ["CFO", "CFI", "CFF", "Net Cash Flow"]
    values = [cfo, cfi, cff, net]

    fig, ax = plt.subplots(figsize=(5.2, 3.0), dpi=150)
    cumulative = 0
    for i, (label, val) in enumerate(zip(labels, values)):
        val = val if pd.notna(val) else 0
        if label == "Net Cash Flow":
            ax.bar(i, val, color="#1565C0")
        else:
            color = "#2E7D32" if val >= 0 else "#C62828"
            ax.bar(i, val, bottom=cumulative if val >= 0 else cumulative + val, color=color)
            cumulative += val
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title("Cash Flow Waterfall (Latest Year)", fontsize=10)
    ax.set_ylabel("Rs. Cr", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    path = os.path.join(CHART_TMP_DIR, f"{ticker}_cf.png")
    fig.savefig(path)
    plt.close(fig)
    return path


def build_tearsheet(cid, company_name, sector, fr_latest, proscons_row, cf_row, bs_hist):
    out_path = os.path.join(OUT_DIR, f"{cid}_tearsheet.pdf")
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = []

    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=16)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=11, textColor=colors.grey)

    story.append(Paragraph(f"{company_name} ({cid})", title_style))
    story.append(Paragraph(f"Sector: {sector}", subtitle_style))
    story.append(Spacer(1, 12))

    kpi_rows = [wrap_row(["Metric", "Value"], header_cell_style)]
    if fr_latest is not None:
        kpi_rows += [
            wrap_row(["Revenue CAGR (5yr)", fmt(fr_latest.get("revenue_cagr_5yr"), "%")]),
            wrap_row(["Profit (PAT) CAGR (5yr)", fmt(fr_latest.get("pat_cagr_5yr"), "%")]),
            wrap_row(["Return on Equity", fmt(fr_latest.get("return_on_equity_pct"), "%")]),
            wrap_row(["Debt to Equity", fmt(fr_latest.get("debt_to_equity"), "", 2)]),
            wrap_row(["Interest Coverage", fmt(fr_latest.get("interest_coverage"), "x")]),
            wrap_row(["Operating Margin", fmt(fr_latest.get("operating_profit_margin_pct"), "%")]),
            wrap_row(["Dividend Payout Ratio", fmt(fr_latest.get("dividend_payout_ratio_pct"), "%")]),
        ]
    else:
        kpi_rows.append(wrap_row(["Data", "Limited financial ratio data available for this company"]))

    kpi_table = Table(kpi_rows, colWidths=[8 * cm, 8 * cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(proscons_row["Pros"], pro_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(proscons_row["Cons"], con_style))
    story.append(PageBreak())

    # ---------- PAGE 2 ----------
    story.append(Paragraph(f"{cid} — Financial Charts & Assessment", styles["Heading1"]))
    story.append(Spacer(1, 8))

    if cf_row is not None:
        bs_chart = make_balance_sheet_chart(bs_hist, cid)
        cf_chart = make_cashflow_waterfall(cf_row["CFO"], cf_row["CFI"], cf_row["CFF"], cf_row["NetCashFlow"], cid)
        story.append(Image(bs_chart, width=16 * cm, height=9.2 * cm))
        story.append(Spacer(1, 10))
        story.append(Image(cf_chart, width=16 * cm, height=9.2 * cm))
        story.append(Spacer(1, 14))
    else:
        story.append(Paragraph("Cash flow / balance sheet data not available for this company.", styles["Normal"]))
        story.append(Spacer(1, 14))

    story.append(Paragraph("Pros", ParagraphStyle("pros_head", parent=styles["Heading3"], textColor=colors.HexColor("#1a7a1a"))))
    for pro in proscons_row["Pros"].split("; "):
        story.append(Paragraph(f"+ {pro}", pro_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Cons", ParagraphStyle("cons_head", parent=styles["Heading3"], textColor=colors.HexColor("#b02a2a"))))
    for con in proscons_row["Cons"].split("; "):
        story.append(Paragraph(f"- {con}", con_style))
    story.append(Spacer(1, 14))

    allocation = cf_row["Capital_Allocation"] if cf_row is not None else "Unknown"
    badge_color = {
        "Self-funded Expansion": colors.HexColor("#2E7D32"),
        "Debt/Equity-funded Expansion": colors.HexColor("#1565C0"),
        "Deleveraging": colors.HexColor("#6A1B9A"),
        "Distress": colors.HexColor("#C62828"),
        "Balanced": colors.HexColor("#616161"),
    }.get(allocation, colors.grey)

    badge_table = Table([[Paragraph(f"Capital Allocation: {allocation}",
                                     ParagraphStyle("badge", parent=styles["Normal"], fontSize=11,
                                                     textColor=colors.white, fontName="Helvetica-Bold"))]],
                         colWidths=[16 * cm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(badge_table)

    doc.build(story)
    size_kb = os.path.getsize(out_path) / 1024
    return out_path, size_kb


def run_batch(tickers_filter=None):
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    bs_all = pd.read_sql("SELECT * FROM balancesheet", conn)
    conn.close()

    fr["year_dt"] = pd.to_datetime(fr["year"], format="%b %Y", errors="coerce")
    bs_all["year_dt"] = pd.to_datetime(bs_all["year"], format="%Y-%m", errors="coerce")

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    proscons = pd.read_csv(PROSCONS_PATH).set_index("company_id")
    cf_summary = pd.read_excel(CASHFLOW_PATH, sheet_name="Summary").set_index("company_id")

    tickers = list(companies["id"]) if tickers_filter is None else tickers_filter
    results, skipped = [], []

    for cid in tickers:
        comp_row = companies[companies["id"] == cid]
        if comp_row.empty:
            skipped.append((cid, "not found in companies table"))
            continue
        company_name = comp_row.iloc[0]["company_name"]
        sector = sector_map.get(cid, "Unknown")

        bs_hist = bs_all[bs_all["company_id"] == cid].sort_values("year_dt").dropna(subset=["year_dt"])
        if len(bs_hist) < 3:
            skipped.append((cid, "fewer than 3 years of balance sheet data"))
            continue
        if cid not in cf_summary.index:
            skipped.append((cid, "no cash flow data available"))
            continue

        fr_g = fr[fr["company_id"] == cid].sort_values("year_dt")
        fr_latest = fr_g.iloc[-1] if len(fr_g) > 0 else None

        proscons_row = proscons.loc[cid] if cid in proscons.index else pd.Series({
            "Pros": "No standout strengths identified from available data",
            "Cons": "No major red flags identified from available data",
        })
        cf_row = cf_summary.loc[cid] if cid in cf_summary.index else None

        path, size_kb = build_tearsheet(cid, company_name, sector, fr_latest, proscons_row, cf_row, bs_hist)
        results.append((cid, path, size_kb))
        print(f"  {cid}: {path} ({size_kb:.1f} KB)")

    if skipped:
        pd.DataFrame(skipped, columns=["Ticker", "Reason"]).to_csv("output/skipped_tearsheets.csv", index=False)
        print(f"Skipped {len(skipped)} tickers (logged to output/skipped_tearsheets.csv)")

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_batch(tickers_filter=sys.argv[1:])
    else:
        run_batch()
