"""Annual Reports Screen — Day 25 deliverable."""

import os
import sys
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "dashboard", "utils"))

from db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports — N100 Analytics", layout="wide")
st.title("📄 Annual Reports")
st.caption("Direct links to BSE annual report PDFs for all 92 companies.")

companies = get_companies()
name_map = dict(zip(companies["id"], companies["company_name"]))

search = st.text_input("Search company", placeholder="e.g. RELIANCE")
if search:
    matches = companies[
        companies["id"].str.contains(search.upper(), na=False) |
        companies["company_name"].str.upper().str.contains(search.upper(), na=False)
    ]
else:
    matches = companies

selected = st.selectbox(
    "Select company",
    matches["id"].tolist(),
    format_func=lambda x: f"{x} — {name_map.get(x, x)}"
)

docs = get_documents(selected)

if docs.empty:
    st.warning(f"No annual reports found for {selected}.")
else:
    st.subheader(f"{name_map.get(selected, selected)} — Annual Reports")
    st.caption(f"{len(docs)} report(s) available")

    for _, row in docs.iterrows():
        year = row.get("year", "N/A")
        url = row.get("annual_report") or row.get("Annual_Report", "")

        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"**FY {year}**")
        with col2:
            if url and str(url) != "nan" and str(url).startswith("http"):
                st.markdown(f"[📥 Download Annual Report]({url})")
            else:
                st.markdown("🔴 **Report unavailable**")
