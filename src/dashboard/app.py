"""N100 Financial Intelligence Platform — Streamlit Dashboard.

Main entry point. Run with: streamlit run src/dashboard/app.py

DAD-PROJ-001 Sprint 4, Day 22 deliverable.
8 screens — all loaded via Streamlit multi-page navigation.
"""

import os
import sys

import streamlit as st

# Make project root importable
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Page configuration — must be the very first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar branding
# ---------------------------------------------------------------------------
st.sidebar.title("📊 N100 Analytics")
st.sidebar.caption("Nifty 100 Financial Intelligence Platform")
st.sidebar.divider()

st.sidebar.markdown("""
**Navigate:**
- 🏠 Home / Overview
- 🏢 Company Profile
- 🔍 Financial Screener
- 👥 Peer Comparison
- 📈 Trend Analysis
- 🏭 Sector Analysis
- 💰 Capital Allocation
- 📄 Annual Reports
""")

st.sidebar.divider()
st.sidebar.caption("v1.0 · 92 Companies · 30+ KPIs")
st.sidebar.caption("Data: Screener.in / BSE India")

# ---------------------------------------------------------------------------
# Home page content (shown when app.py is loaded directly)
# ---------------------------------------------------------------------------
st.title("📊 Nifty 100 Financial Intelligence Platform")
st.markdown("""
Welcome to the N100 Analytics Dashboard — a production-grade financial
intelligence system covering all **92 Nifty 100 companies**.

### Quick Navigation
Use the **sidebar** (left) to navigate between screens, or select a page
from the list below:

| Screen | Description |
|--------|-------------|
| 🏠 **Home** | Summary KPIs, sector breakdown, top companies |
| 🏢 **Company Profile** | Full financial profile for any of 92 tickers |
| 🔍 **Screener** | Filter companies by 15 metrics, 6 preset templates |
| 👥 **Peer Comparison** | Percentile rankings across 11 peer groups |
| 📈 **Trend Analysis** | 10-year metric trends with YoY annotations |
| 🏭 **Sector Analysis** | Bubble charts, median KPIs by sector |
| 💰 **Capital Allocation** | Treemap of 92 companies by cash flow pattern |
| 📄 **Annual Reports** | Direct links to BSE annual report PDFs |

---
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Companies Covered", "92", "Nifty 100")
with col2:
    st.metric("Financial KPIs", "30+", "Per company")
with col3:
    st.metric("Data History", "10–13 years", "FY 2010–2024")

st.info("👈 Select a screen from the sidebar to begin exploring.")
