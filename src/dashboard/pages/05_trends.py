"""Trend Analysis Screen — Day 25 deliverable."""

import os
import sys
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))

from db import get_companies, get_pl, get_ratios

st.set_page_config(page_title="Trend Analysis — N100 Analytics", layout="wide")
st.title("📈 Trend Analysis")
st.caption("10-year metric trends with year-over-year % change annotations.")

companies = get_companies()
name_map = dict(zip(companies["id"], companies["company_name"]))

search = st.text_input("Search company", placeholder="e.g. INFY")
if search:
    matches = companies[
        companies["id"].str.contains(search.upper(), na=False) |
        companies["company_name"].str.upper().str.contains(search.upper(), na=False)
    ]
else:
    matches = companies

selected = st.selectbox("Select company", matches["id"].tolist(),
                        format_func=lambda x: f"{x} — {name_map.get(x,x)}")

METRICS = {
    "Sales (Revenue)": ("pl", "sales"),
    "Net Profit": ("pl", "net_profit"),
    "OPM %": ("pl", "opm_percentage"),
    "ROE %": ("ratios", "return_on_equity_pct"),
    "D/E Ratio": ("ratios", "debt_to_equity"),
    "FCF (₹ Cr)": ("ratios", "free_cash_flow_cr"),
}

selected_metrics = st.multiselect(
    "Select metrics (up to 3)",
    list(METRICS.keys()),
    default=["Sales (Revenue)", "Net Profit"],
    max_selections=3,
)

if not selected_metrics:
    st.info("Select at least one metric above.")
    st.stop()

pl = get_pl(selected)
ratios = get_ratios(selected)

fig = go.Figure()
for metric_label in selected_metrics:
    source, col = METRICS[metric_label]
    df = pl if source == "pl" else ratios
    if df.empty or col not in df.columns:
        continue
    df_sorted = df.sort_values("year").dropna(subset=[col])
    values = df_sorted[col].tolist()
    years = df_sorted["year"].tolist()

    yoy = [None] + [
        round((values[i] - values[i-1]) / abs(values[i-1]) * 100, 1)
        if values[i-1] != 0 else None
        for i in range(1, len(values))
    ]

    fig.add_trace(go.Scatter(
        x=years, y=values, mode="lines+markers",
        name=metric_label,
        text=[f"{v:+.1f}%" if v is not None else "" for v in yoy],
        textposition="top center",
    ))

fig.update_layout(height=450, yaxis_title="Value", xaxis_title="Year",
                  legend=dict(orientation="h", yanchor="bottom", y=1.02),
                  margin=dict(t=40, b=20))
st.plotly_chart(fig, use_container_width=True)
