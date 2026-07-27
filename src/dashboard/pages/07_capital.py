"""Capital Allocation Screen — Day 25 deliverable."""
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))

from db import get_companies, get_financial_ratios

st.set_page_config(page_title="Capital Allocation — N100 Analytics", layout="wide")
st.title("💰 Capital Allocation Map")
st.caption("Treemap of 92 companies by cash flow patterns — click a pattern to drill down.")

try:
    companies = get_companies()
    ratios = get_financial_ratios()
    
    if companies.empty or ratios.empty:
        st.warning("⚠️ Data not available yet. Check database connection.")
    else:
        # Create simple allocation by FCF
        allocation_data = ratios.groupby("company_id").agg({
            "free_cash_flow_cr": "sum"
        }).reset_index()
        
        allocation_data = allocation_data.merge(
            companies[["id", "company_name"]], 
            left_on="company_id", right_on="id", how="left"
        )
        
        allocation_data = allocation_data[allocation_data["free_cash_flow_cr"] > 0]
        
        if allocation_data.empty:
            st.info("ℹ️ No cash flow data available for visualization.")
        else:
            fig = px.treemap(
                allocation_data,
                labels="company_name",
                values="free_cash_flow_cr",
                title="Capital Allocation by Free Cash Flow (₹ Cr)"
            )
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Error loading data: {str(e)}")
    st.info("This page requires complete data. Some source files may be missing.")