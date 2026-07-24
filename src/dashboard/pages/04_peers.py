"""Peer Comparison Screen — Day 24 deliverable.

Peer group dropdown, radar chart, side-by-side KPI table.
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))

from db import get_peers, get_peer_percentiles, get_screener_universe, get_companies

st.set_page_config(page_title="Peer Comparison — N100 Analytics", layout="wide")
st.title("👥 Peer Comparison")
st.caption("Compare companies within their peer group across 10 financial metrics.")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
peers_df = get_peers()
universe = get_screener_universe()
companies = get_companies()
name_map = dict(zip(companies["id"], companies["company_name"]))

# ---------------------------------------------------------------------------
# Peer group selector
# ---------------------------------------------------------------------------
group_names = sorted(peers_df["peer_group_name"].unique().tolist())
selected_group = st.selectbox("Select Peer Group", group_names)

group_members = peers_df[peers_df["peer_group_name"] == selected_group]
benchmark_id = group_members[group_members["is_benchmark"] == 1]["company_id"].values
benchmark_id = benchmark_id[0] if len(benchmark_id) > 0 else None
member_ids = group_members["company_id"].tolist()

group_data = universe[universe["company_id"].isin(member_ids)].copy()
group_data["company_name"] = group_data["company_id"].map(name_map)

st.caption(f"**{len(member_ids)} companies** · Benchmark: **{benchmark_id or 'N/A'}**")

# ---------------------------------------------------------------------------
# Company selector for radar chart
# ---------------------------------------------------------------------------
selected_company = st.selectbox(
    "Select company for radar chart",
    member_ids,
    format_func=lambda x: f"{x} — {name_map.get(x, x)}"
)

# ---------------------------------------------------------------------------
# Radar chart
# ---------------------------------------------------------------------------
RADAR_METRICS = [
    "return_on_equity_pct", "net_profit_margin_pct",
    "debt_to_equity", "free_cash_flow_cr",
    "asset_turnover", "earnings_per_share",
    "dividend_yield_pct", "composite_quality_score",
]
RADAR_LABELS = ["ROE %", "NPM %", "D/E", "FCF", "Asset T/O", "EPS", "Div Yield", "Quality Score"]

# Compute composite score for display
from engine import load_config, compute_composite_score
import sys as _sys
_sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "screener"))
config = load_config()
group_data["composite_quality_score"] = compute_composite_score(group_data, config)

def normalise_group(df, metrics):
    result = {}
    for m in metrics:
        if m not in df.columns:
            result[m] = {cid: 0.5 for cid in df["company_id"]}
            continue
        series = df.set_index("company_id")[m].fillna(0)
        if m == "debt_to_equity":
            series = 1 / (series + 0.01)
        rng = series.max() - series.min()
        if rng == 0:
            result[m] = {cid: 0.5 for cid in df["company_id"]}
        else:
            result[m] = ((series - series.min()) / rng).to_dict()
    return result

norm = normalise_group(group_data, RADAR_METRICS)

company_vals = [norm[m].get(selected_company, 0.5) for m in RADAR_METRICS]
group_avg = [
    sum(norm[m].values()) / len(norm[m]) if norm[m] else 0.5
    for m in RADAR_METRICS
]

fig_radar = go.Figure()

# Group average
fig_radar.add_trace(go.Scatterpolar(
    r=group_avg + [group_avg[0]],
    theta=RADAR_LABELS + [RADAR_LABELS[0]],
    fill="none", mode="lines",
    line=dict(color="grey", dash="dash", width=2),
    name=f"{selected_group} Avg"
))

# Selected company
fig_radar.add_trace(go.Scatterpolar(
    r=company_vals + [company_vals[0]],
    theta=RADAR_LABELS + [RADAR_LABELS[0]],
    fill="toself", mode="lines+markers",
    line=dict(color="#2E86AB", width=2),
    fillcolor="rgba(46,134,171,0.2)",
    name=selected_company
))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    showlegend=True,
    height=450,
    title=f"{name_map.get(selected_company, selected_company)} vs {selected_group} Average",
)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Side-by-side KPI table
# ---------------------------------------------------------------------------
st.subheader(f"{selected_group} — Side-by-Side Comparison")

display_metrics = [
    "company_id", "company_name",
    "return_on_equity_pct", "net_profit_margin_pct",
    "debt_to_equity", "free_cash_flow_cr",
    "asset_turnover", "interest_coverage",
    "pe_ratio", "pb_ratio", "composite_quality_score",
]
available = [c for c in display_metrics if c in group_data.columns]
table_df = group_data[available].copy()

# Highlight benchmark row
def highlight_benchmark(row):
    if row.get("company_id") == benchmark_id:
        return ["background-color: #FFF3CD"] * len(row)
    return [""] * len(row)

table_df = table_df.round(2)
table_df.columns = [c.replace("_", " ").title() for c in available]

st.dataframe(
    table_df.reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)
st.caption(f"🏆 Benchmark company: **{benchmark_id}** (highlighted in yellow)")
