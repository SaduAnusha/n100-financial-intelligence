"""Financial Screener Screen — Day 24 deliverable.

10 metric sliders, 6 preset buttons, live results table, CSV download.
"""

import io
import os
import sys

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "screener"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "analytics"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "etl"))

from db import get_screener_universe
from engine import load_config, compute_composite_score, run_preset

st.set_page_config(page_title="Screener — N100 Analytics", layout="wide")
st.title("🔍 Financial Screener")
st.caption("Filter all 92 Nifty 100 companies by key financial metrics.")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
config = load_config()
universe = get_screener_universe()
universe["composite_quality_score"] = compute_composite_score(universe, config)

# ---------------------------------------------------------------------------
# Preset buttons
# ---------------------------------------------------------------------------
st.subheader("Quick Presets")
preset_cols = st.columns(6)
preset_names = list(config["presets"].keys())
preset_labels = ["⭐ Quality", "💰 Value", "🚀 Growth", "💵 Dividend", "🏦 Debt-Free", "🔄 Turnaround"]

selected_preset = None
for i, (name, label) in enumerate(zip(preset_names, preset_labels)):
    if preset_cols[i].button(label, use_container_width=True):
        selected_preset = name

# Apply preset filters to session state
if selected_preset:
    preset_config = config["presets"][selected_preset]
    st.session_state["active_preset"] = selected_preset
    st.session_state["preset_filters"] = preset_config.get("filters", {})

# ---------------------------------------------------------------------------
# Sidebar sliders
# ---------------------------------------------------------------------------
st.sidebar.header("Filter Settings")

if "preset_filters" in st.session_state:
    pf = st.session_state["preset_filters"]
    st.sidebar.info(f"Preset: {st.session_state.get('active_preset', '')}")
else:
    pf = {}

def _get(col, op, default):
    return pf.get(col, {}).get(op, default)

min_roe = st.sidebar.slider("Min ROE %", 0.0, 50.0, float(_get("return_on_equity_pct", "min", 0.0)), 1.0)
max_de = st.sidebar.slider("Max D/E", 0.0, 10.0, float(_get("debt_to_equity", "max", 10.0)), 0.1)
min_fcf = st.sidebar.slider("Min FCF (₹ Cr)", -5000.0, 50000.0, float(_get("free_cash_flow_cr", "min", -5000.0)), 500.0)
min_npm = st.sidebar.slider("Min Net Profit Margin %", 0.0, 40.0, 0.0, 1.0)
min_opm = st.sidebar.slider("Min OPM %", 0.0, 50.0, 0.0, 1.0)
max_pe = st.sidebar.slider("Max P/E", 5.0, 100.0, float(_get("pe_ratio", "max", 100.0)), 1.0)
max_pb = st.sidebar.slider("Max P/B", 0.5, 20.0, float(_get("pb_ratio", "max", 20.0)), 0.5)
min_div_yield = st.sidebar.slider("Min Dividend Yield %", 0.0, 5.0, float(_get("dividend_yield_pct", "min", 0.0)), 0.1)
min_rev_cagr = st.sidebar.slider("Min Revenue CAGR 5yr %", 0.0, 30.0, 0.0, 1.0)
min_pat_cagr = st.sidebar.slider("Min PAT CAGR 5yr %", 0.0, 40.0, float(_get("pat_cagr_5yr", "min", 0.0)), 1.0)

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
filtered = universe.copy()

def safe_filter(df, col, op, val):
    if col not in df.columns:
        return df
    if op == "min":
        return df[df[col].notna() & (df[col] >= val)]
    elif op == "max":
        # Financials pass D/E filter automatically
        if col == "debt_to_equity" and "broad_sector" in df.columns:
            fin_mask = df["broad_sector"] == "Financials"
            return df[fin_mask | (df[col].notna() & (df[col] <= val))]
        return df[df[col].isna() | (df[col] <= val)]
    return df

filtered = safe_filter(filtered, "return_on_equity_pct", "min", min_roe)
filtered = safe_filter(filtered, "debt_to_equity", "max", max_de)
filtered = safe_filter(filtered, "free_cash_flow_cr", "min", min_fcf)
filtered = safe_filter(filtered, "net_profit_margin_pct", "min", min_npm)
filtered = safe_filter(filtered, "operating_profit_margin_pct", "min", min_opm)
filtered = safe_filter(filtered, "pe_ratio", "max", max_pe)
filtered = safe_filter(filtered, "pb_ratio", "max", max_pb)
filtered = safe_filter(filtered, "dividend_yield_pct", "min", min_div_yield)
if "revenue_cagr_5yr" in filtered.columns:
    filtered = safe_filter(filtered, "revenue_cagr_5yr", "min", min_rev_cagr)
if "pat_cagr_5yr" in filtered.columns:
    filtered = safe_filter(filtered, "pat_cagr_5yr", "min", min_pat_cagr)

filtered = filtered.sort_values("composite_quality_score", ascending=False)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
st.subheader(f"Results — {len(filtered)} companies match your filters")

display_cols = [
    "company_id", "company_name", "broad_sector",
    "composite_quality_score", "return_on_equity_pct",
    "debt_to_equity", "free_cash_flow_cr",
    "net_profit_margin_pct", "pe_ratio", "pb_ratio",
    "dividend_yield_pct",
]
available = [c for c in display_cols if c in filtered.columns]
display_df = filtered[available].copy()
display_df.columns = [c.replace("_", " ").title() for c in available]

st.dataframe(display_df, use_container_width=True, hide_index=True, height=450)

# ---------------------------------------------------------------------------
# CSV Download
# ---------------------------------------------------------------------------
csv_buffer = io.StringIO()
filtered[available].to_csv(csv_buffer, index=False)
st.download_button(
    label="⬇️ Download CSV",
    data=csv_buffer.getvalue(),
    file_name="screener_results.csv",
    mime="text/csv",
)
