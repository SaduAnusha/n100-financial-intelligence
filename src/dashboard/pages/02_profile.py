"""Company Profile Screen — Day 23 deliverable.

Search by ticker or name, view full financial profile,
10-year charts, KPI tiles, pros and cons.
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    get_companies, get_pl, get_bs, get_cf, get_ratios, get_screener_universe
)

st.set_page_config(page_title="Company Profile — N100 Analytics", layout="wide")
st.title("🏢 Company Profile")

# ---------------------------------------------------------------------------
# Company search
# ---------------------------------------------------------------------------
companies = get_companies()
ticker_list = companies["id"].tolist()
name_map = dict(zip(companies["id"], companies["company_name"]))

search = st.text_input("Search by ticker or company name", placeholder="e.g. TCS or Tata Consultancy")

# Filter matching companies
if search:
    search_upper = search.upper().strip()
    matches = companies[
        companies["id"].str.contains(search_upper, na=False) |
        companies["company_name"].str.upper().str.contains(search_upper, na=False)
    ]
else:
    matches = companies

if matches.empty:
    st.error("❌ Ticker not found — please try another.")
    st.stop()

# Dropdown to select from matches
selected_ticker = st.selectbox(
    "Select company",
    options=matches["id"].tolist(),
    format_func=lambda x: f"{x} — {name_map.get(x, x)}"
)

if not selected_ticker:
    st.info("👆 Search for a company above to view its profile.")
    st.stop()

# ---------------------------------------------------------------------------
# Load company data
# ---------------------------------------------------------------------------
company_row = companies[companies["id"] == selected_ticker].iloc[0]

with st.spinner(f"Loading {selected_ticker} profile..."):
    pl = get_pl(selected_ticker)
    bs = get_bs(selected_ticker)
    cf = get_cf(selected_ticker)
    ratios = get_ratios(selected_ticker)

# ---------------------------------------------------------------------------
# Company card
# ---------------------------------------------------------------------------
st.divider()
col_info, col_meta = st.columns([2, 1])

with col_info:
    st.subheader(f"{company_row['company_name']}")
    st.caption(f"**{selected_ticker}** · {company_row.get('broad_sector', 'N/A')} · {company_row.get('sub_sector', 'N/A')}")
    about = company_row.get("about_company", "")
    if about and str(about) != "nan":
        st.markdown(str(about)[:400] + ("..." if len(str(about)) > 400 else ""))

with col_meta:
    if company_row.get("website") and str(company_row["website"]) != "nan":
        st.markdown(f"🌐 [Website]({company_row['website']})")
    if company_row.get("nse_profile") and str(company_row["nse_profile"]) != "nan":
        st.markdown(f"📈 [NSE Profile]({company_row['nse_profile']})")
    st.metric("Face Value", f"₹{company_row.get('face_value', 'N/A')}")

st.divider()

# ---------------------------------------------------------------------------
# 6 KPI tiles (latest year from ratios)
# ---------------------------------------------------------------------------
st.subheader("Latest KPIs")

if not ratios.empty:
    latest = ratios.sort_values("year").iloc[-1]
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("ROE", f"{latest.get('return_on_equity_pct', 'N/A'):.1f}%" if pd.notna(latest.get('return_on_equity_pct')) else "N/A")
    k2.metric("Net Profit Margin", f"{latest.get('net_profit_margin_pct', 'N/A'):.1f}%" if pd.notna(latest.get('net_profit_margin_pct')) else "N/A")
    k3.metric("D/E", f"{latest.get('debt_to_equity', 'N/A'):.2f}" if pd.notna(latest.get('debt_to_equity')) else "N/A")
    k4.metric("ICR", f"{latest.get('interest_coverage', 'N/A'):.1f}x" if pd.notna(latest.get('interest_coverage')) else "Debt Free")
    k5.metric("Asset Turnover", f"{latest.get('asset_turnover', 'N/A'):.2f}x" if pd.notna(latest.get('asset_turnover')) else "N/A")
    k6.metric("FCF (₹ Cr)", f"{latest.get('free_cash_flow_cr', 'N/A'):,.0f}" if pd.notna(latest.get('free_cash_flow_cr')) else "N/A")
else:
    st.warning("No ratio data available for this company.")

st.divider()

# ---------------------------------------------------------------------------
# 10-year Revenue and Net Profit bar chart
# ---------------------------------------------------------------------------
if not pl.empty:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Revenue & Net Profit (10yr)")
        fig_pl = go.Figure()
        fig_pl.add_trace(go.Bar(
            x=pl["year"], y=pl["sales"],
            name="Revenue", marker_color="#2E86AB"
        ))
        fig_pl.add_trace(go.Bar(
            x=pl["year"], y=pl["net_profit"],
            name="Net Profit", marker_color="#A23B72"
        ))
        fig_pl.update_layout(
            barmode="group", height=350,
            margin=dict(t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis_title="₹ Crore",
        )
        st.plotly_chart(fig_pl, use_container_width=True)

    with col_chart2:
        st.subheader("ROE & Net Profit Margin (10yr)")
        if not ratios.empty:
            fig_roe = go.Figure()
            fig_roe.add_trace(go.Scatter(
                x=ratios["year"], y=ratios["return_on_equity_pct"],
                mode="lines+markers", name="ROE %", line=dict(color="#2E86AB", width=2)
            ))
            fig_roe.add_trace(go.Scatter(
                x=ratios["year"], y=ratios["net_profit_margin_pct"],
                mode="lines+markers", name="NPM %",
                line=dict(color="#A23B72", width=2, dash="dash")
            ))
            fig_roe.update_layout(
                height=350,
                margin=dict(t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                yaxis_title="%",
            )
            st.plotly_chart(fig_roe, use_container_width=True)
        else:
            st.info("No ratio trend data available.")

st.divider()

# ---------------------------------------------------------------------------
# Cash flow bar chart
# ---------------------------------------------------------------------------
if not cf.empty:
    st.subheader("Cash Flow Components (10yr)")
    fig_cf = go.Figure()
    fig_cf.add_trace(go.Bar(x=cf["year"], y=cf["operating_activity"],
                             name="CFO", marker_color="#27AE60"))
    fig_cf.add_trace(go.Bar(x=cf["year"], y=cf["investing_activity"],
                             name="CFI", marker_color="#E74C3C"))
    fig_cf.add_trace(go.Bar(x=cf["year"], y=cf["financing_activity"],
                             name="CFF", marker_color="#F39C12"))
    fig_cf.update_layout(
        barmode="group", height=300,
        margin=dict(t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        yaxis_title="₹ Crore",
    )
    st.plotly_chart(fig_cf, use_container_width=True)

st.caption(f"Data as of latest available year · All values in ₹ Crore")
