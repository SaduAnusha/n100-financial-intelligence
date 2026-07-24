"""Home / Overview Screen — Day 23 deliverable.

Shows summary KPIs, sector breakdown donut chart,
and top companies by composite quality score.
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
for p in [
    PROJECT_ROOT,
    os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"),
    os.path.join(PROJECT_ROOT, "src", "screener"),
    os.path.join(PROJECT_ROOT, "src", "analytics"),
    os.path.join(PROJECT_ROOT, "src", "etl"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from db import (
    get_companies, get_ratios, get_sectors, get_screener_universe
)

st.set_page_config(page_title="Home — N100 Analytics", layout="wide")
st.title("🏠 Nifty 100 — Market Overview")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with st.spinner("Loading market data..."):
    companies = get_companies()
    sectors = get_sectors()
    universe = get_screener_universe()

# Year selector in sidebar
st.sidebar.header("Filters")
available_years = ["Latest"] + [str(y) for y in range(2024, 2018, -1)]
selected_year = st.sidebar.selectbox("Reference Year", available_years)

# ---------------------------------------------------------------------------
# Summary KPI tiles
# ---------------------------------------------------------------------------
st.subheader("Market Summary")

col1, col2, col3, col4, col5, col6 = st.columns(6)

avg_roe = universe["return_on_equity_pct"].mean()
median_pe = universe["pe_ratio"].median()
median_de = universe["debt_to_equity"].median()
total_cos = len(companies)
debt_free = (universe["debt_to_equity"] == 0).sum()
median_rev_cagr = universe["revenue_cagr_5yr"].median() if "revenue_cagr_5yr" in universe.columns else None

col1.metric("Avg ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
col2.metric("Median P/E", f"{median_pe:.1f}x" if pd.notna(median_pe) else "N/A")
col3.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
col4.metric("Total Companies", total_cos)
col5.metric("Debt-Free Cos", int(debt_free))
col6.metric("Median Rev CAGR 5yr",
            f"{median_rev_cagr:.1f}%" if median_rev_cagr and pd.notna(median_rev_cagr) else "N/A")

st.divider()

# ---------------------------------------------------------------------------
# Two column layout: donut chart + top companies table
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Sector Breakdown")
    sector_counts = sectors.groupby("broad_sector")["company_id"].count().reset_index()
    sector_counts.columns = ["Sector", "Companies"]
    sector_counts = sector_counts.sort_values("Companies", ascending=False)

    fig_donut = px.pie(
        sector_counts,
        values="Companies",
        names="Sector",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_donut.update_layout(
        showlegend=True,
        margin=dict(t=20, b=20, l=20, r=20),
        height=380,
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.subheader("Top 10 by Composite Quality Score")

    # Compute composite score
    from engine import load_config, compute_composite_score
    config = load_config()
    universe["composite_quality_score"] = compute_composite_score(universe, config)

    top10 = universe.nlargest(10, "composite_quality_score")[
        ["company_id", "company_name", "broad_sector",
         "composite_quality_score", "return_on_equity_pct", "debt_to_equity"]
    ].copy()
    top10.columns = ["Ticker", "Company", "Sector", "Score", "ROE %", "D/E"]
    top10["Score"] = top10["Score"].round(1)
    top10["ROE %"] = top10["ROE %"].round(1)
    top10["D/E"] = top10["D/E"].round(2)

    st.dataframe(
        top10.reset_index(drop=True),
        use_container_width=True,
        height=380,
        hide_index=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Sector median KPI bar chart
# ---------------------------------------------------------------------------
st.subheader("Sector Median ROE")

sector_roe = universe.merge(
    sectors[["company_id", "broad_sector"]], on="company_id", how="left", suffixes=("", "_s")
)
sector_col = "broad_sector_s" if "broad_sector_s" in sector_roe.columns else "broad_sector"
sector_med = sector_roe.groupby(sector_col)["return_on_equity_pct"].median().reset_index()
sector_med.columns = ["Sector", "Median ROE %"]
sector_med = sector_med.sort_values("Median ROE %", ascending=True)

fig_bar = px.bar(
    sector_med,
    x="Median ROE %",
    y="Sector",
    orientation="h",
    color="Median ROE %",
    color_continuous_scale="Blues",
    text="Median ROE %",
)
fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_bar.update_layout(
    height=350,
    margin=dict(t=20, b=20, l=20, r=20),
    coloraxis_showscale=False,
)
st.plotly_chart(fig_bar, use_container_width=True)
