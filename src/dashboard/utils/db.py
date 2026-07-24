"""Shared data loader for the N100 Streamlit Dashboard.

All functions use @st.cache_data(ttl=600) so database queries are
cached for 10 minutes — prevents re-querying SQLite on every
Streamlit re-render, keeping the dashboard fast.

DAD-PROJ-001 Sprint 4, Day 22 deliverable.
"""

import os
import sqlite3
from typing import Optional

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "db", "nifty100.db")
SUPPORTING_DIR = os.path.join(PROJECT_ROOT, "data", "supporting")
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")


def _get_conn() -> sqlite3.Connection:
    """Return a SQLite connection with FK enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Company master data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Load all 92 companies with sector info."""
    conn = _get_conn()
    df = pd.read_sql("""
        SELECT c.id, c.company_name, c.about_company,
               c.face_value, c.book_value, c.roe_percentage,
               c.roce_percentage, c.website, c.nse_profile,
               s.broad_sector, s.sub_sector, s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        ORDER BY c.company_name
    """, conn)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Financial ratios
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_ratios(ticker: Optional[str] = None, year: Optional[str] = None) -> pd.DataFrame:
    """Load financial ratios — optionally filtered by ticker and/or year."""
    conn = _get_conn()
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper().strip())
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY company_id, year"
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# P&L, Balance Sheet, Cash Flow
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Load P&L history for a company."""
    conn = _get_conn()
    df = pd.read_sql(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=[ticker.upper().strip()]
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Load balance sheet history for a company."""
    conn = _get_conn()
    df = pd.read_sql(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=[ticker.upper().strip()]
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Load cash flow history for a company."""
    conn = _get_conn()
    df = pd.read_sql(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=[ticker.upper().strip()]
    )
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Sectors
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Load sector mapping for all companies."""
    conn = _get_conn()
    df = pd.read_sql("SELECT * FROM sectors ORDER BY broad_sector", conn)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Peer groups
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_peers(group_name: Optional[str] = None) -> pd.DataFrame:
    """Load peer group data — optionally filtered by group name."""
    conn = _get_conn()
    if group_name:
        df = pd.read_sql(
            "SELECT * FROM peer_groups WHERE peer_group_name = ?",
            conn, params=[group_name]
        )
    else:
        df = pd.read_sql("SELECT * FROM peer_groups ORDER BY peer_group_name", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name: Optional[str] = None) -> pd.DataFrame:
    """Load peer percentile rankings."""
    conn = _get_conn()
    if group_name:
        df = pd.read_sql(
            "SELECT * FROM peer_percentiles WHERE peer_group_name = ?",
            conn, params=[group_name]
        )
    else:
        df = pd.read_sql("SELECT * FROM peer_percentiles", conn)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Valuation / Market Cap
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_valuation(ticker: Optional[str] = None) -> pd.DataFrame:
    """Load valuation multiples from market_cap table."""
    conn = _get_conn()
    if ticker:
        df = pd.read_sql(
            "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year",
            conn, params=[ticker.upper().strip()]
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM market_cap ORDER BY company_id, year", conn
        )
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Capital allocation
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_capital_allocation() -> pd.DataFrame:
    """Load capital allocation patterns from output CSV."""
    path = os.path.join(PROJECT_ROOT, "output", "capital_allocation.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Documents / Annual Reports
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    """Load annual report links for a company."""
    conn = _get_conn()
    df = pd.read_sql(
        "SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC",
        conn, params=[ticker.upper().strip()]
    )
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Composite screener data (joins ratios + market cap + sectors)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def get_screener_universe() -> pd.DataFrame:
    """Load full screener universe — one row per company (latest year)."""
    fr = pd.read_excel(
        os.path.join(SUPPORTING_DIR, "financial_ratios.xlsx"), header=0
    )
    fr["company_id"] = fr["company_id"].astype(str).str.strip().str.upper()
    fr = fr.sort_values("year").groupby("company_id").last().reset_index()

    mc = pd.read_excel(
        os.path.join(SUPPORTING_DIR, "market_cap.xlsx"), header=0
    )
    mc["company_id"] = mc["company_id"].astype(str).str.strip().str.upper()
    mc = mc.sort_values("year").groupby("company_id").last().reset_index()
    mc = mc[["company_id", "market_cap_crore", "pe_ratio", "pb_ratio",
             "ev_ebitda", "dividend_yield_pct"]]

    companies = get_companies()
    sectors = get_sectors()

    df = fr.merge(mc, on="company_id", how="left")
    df = df.merge(
        companies[["id", "company_name"]].rename(columns={"id": "company_id"}),
        on="company_id", how="left"
    )
    df = df.merge(
        sectors[["company_id", "broad_sector", "sub_sector"]],
        on="company_id", how="left"
    )

    # Pull CAGR from SQLite
    conn = _get_conn()
    try:
        cagr = pd.read_sql("""
            SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr,
                   eps_cagr_5yr, return_on_capital_pct
            FROM financial_ratios
        """, conn)
        cagr["company_id"] = cagr["company_id"].astype(str).str.strip().str.upper()
        cagr = cagr.sort_values("year").groupby("company_id").last().reset_index()
        cagr = cagr.drop(columns=["year"])
        df = df.merge(cagr, on="company_id", how="left")
    except Exception:
        pass
    finally:
        conn.close()

    return df
