import os, sys, pandas as pd, streamlit as st
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))
from db import get_companies, get_financial_ratios

st.set_page_config(page_title="Company Profile — N100 Analytics", layout="wide")
st.title("🏢 Company Profile")

try:
    companies = get_companies()
    ratios = get_financial_ratios()
    
    ticker = st.selectbox("Select Company", sorted(companies['company_name'].unique()))
    
    company_data = companies[companies['company_name'] == ticker]
    if not company_data.empty:
        st.metric("Company", ticker)
        
        company_ratios = ratios[ratios['company_id'] == company_data.iloc[0]['id']]
        if not company_ratios.empty:
            latest = company_ratios.iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("ROE %", f"{latest['return_on_equity_pct']:.2f}")
            col2.metric("D/E", f"{latest['debt_to_equity']:.2f}")
            col3.metric("NPM %", f"{latest['net_profit_margin_pct']:.2f}")
        
except Exception as e:
    st.error(f"⚠️ Error: {str(e)}")