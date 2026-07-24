"""Sector Analysis Screen — Day 25 deliverable."""

import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))

from db import get_sectors, get_screener_universe

st.set_page_config(page_title="Sector Analysis — N100 Analytics", layout="wide")
st.title("🏭 Sector Analysis")
st.caption("Bubble charts and median KPIs across 11 sectors.")

sectors = get_sectors()
universe = get_screener_universe()

sector_names = sorted(sectors["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Select Sector", ["All Sectors"] + sector_names)

if selected_sector != "All Sectors":
    sector_cos = sectors[sectors["broad_sector"] == selected_sector]["company_id"].tolist()
    plot_data = universe[universe["company_id"].isin(sector_cos)].copy()
else:
    plot_data = universe.merge(
        sectors[["company_id", "broad_sector", "sub_sector"]],
        on="company_id", how="left", suffixes=("", "_s")
    )

plot_data = plot_data.dropna(subset=["return_on_equity_pct", "market_cap_crore"])

color_col = "broad_sector" if "broad_sector" in plot_data.columns else "company_id"

fig_bubble = px.scatter(
    plot_data,
    x="net_profit_margin_pct",
    y="return_on_equity_pct",
    size="market_cap_crore",
    color=color_col,
    hover_data=["company_id", "company_name"] if "company_name" in plot_data.columns else ["company_id"],
    title="ROE vs Net Profit Margin (bubble size = Market Cap)",
    labels={
        "net_profit_margin_pct": "Net Profit Margin %",
        "return_on_equity_pct": "ROE %",
        "market_cap_crore": "Market Cap (₹ Cr)",
    },
    size_max=60,
)
fig_bubble.update_layout(height=500, margin=dict(t=40, b=20))
st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()
st.subheader("Sector Median KPIs")

sector_med = universe.merge(
    sectors[["company_id", "broad_sector"]], on="company_id", how="left"
).groupby("broad_sector").agg(
    Median_ROE=("return_on_equity_pct", "median"),
    Median_NPM=("net_profit_margin_pct", "median"),
    Median_DE=("debt_to_equity", "median"),
    Median_PE=("pe_ratio", "median"),
    Companies=("company_id", "count"),
).reset_index().round(2)

st.dataframe(sector_med, use_container_width=True, hide_index=True)
