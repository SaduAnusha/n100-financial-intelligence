import os

pages = {
    "01_home.py": """import os, sys, pandas as pd, streamlit as st
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))
from db import get_companies, get_financial_ratios

st.set_page_config(page_title="Home — N100 Analytics", layout="wide")
st.title("Market Overview")
try:
    companies = get_companies()
    ratios = get_financial_ratios()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", len(companies))
    col2.metric("Avg ROE", f"{ratios['return_on_equity_pct'].mean():.1f}%")
    col3.metric("Avg DE", f"{ratios['debt_to_equity'].mean():.2f}")
    col4.metric("Avg NPM", f"{ratios['net_profit_margin_pct'].mean():.1f}%")
    st.divider()
    st.subheader("Top 10 by ROE")
    top_roe = ratios.nlargest(10, 'return_on_equity_pct')[['company_id', 'return_on_equity_pct']]
    st.dataframe(top_roe, use_container_width=True)
except Exception as e:
    st.error(f"Error: {str(e)}")
""",
}

for page, content in pages.items():
    path = f"src/dashboard/pages/{page}"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {page}")

print("All pages fixed!")