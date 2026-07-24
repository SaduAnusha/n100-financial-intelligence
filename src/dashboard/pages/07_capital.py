"""Capital Allocation Map Screen — Day 25 deliverable."""

import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))

from db import get_capital_allocation, get_companies

st.set_page_config(page_title="Capital Allocation — N100 Analytics", layout="wide")
st.title("💰 Capital Allocation Map")
st.caption("Treemap of 92 companies by cash flow pattern — click a pattern to drill down.")

ca = get_capital_allocation()
companies = get_companies()

if ca.empty:
    st.error("capital_allocation.csv not found. Run src/analytics/cashflow_kpis.py first.")
    st.stop()

name_map = dict(zip(companies["id"], companies["company_name"]))

# Use latest year per company
ca["company_id"] = ca["company_id"].astype(str).str.strip().str.upper()
latest_ca = ca.sort_values("year").groupby("company_id").last().reset_index()
latest_ca["company_name"] = latest_ca["company_id"].map(name_map).fillna(latest_ca["company_id"])
latest_ca["count"] = 1

# Treemap
fig = px.treemap(
    latest_ca,
    path=["pattern_label", "company_id"],
    values="count",
    color="pattern_label",
    hover_data=["company_name"],
    color_discrete_sequence=px.colors.qualitative.Set3,
    title="Capital Allocation Patterns — 92 Companies (Latest Year)",
)
fig.update_layout(height=550, margin=dict(t=40, b=10))
fig.update_traces(textinfo="label+value")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Pattern Summary")

summary = latest_ca.groupby("pattern_label")["company_id"].count().reset_index()
summary.columns = ["Pattern", "Companies"]
summary = summary.sort_values("Companies", ascending=False)

col1, col2 = st.columns([1, 2])
with col1:
    st.dataframe(summary, use_container_width=True, hide_index=True)

with col2:
    selected_pattern = st.selectbox("Drill down into pattern", summary["Pattern"].tolist())
    pattern_cos = latest_ca[latest_ca["pattern_label"] == selected_pattern][
        ["company_id", "company_name"]
    ].reset_index(drop=True)
    st.dataframe(pattern_cos, use_container_width=True, hide_index=True)
