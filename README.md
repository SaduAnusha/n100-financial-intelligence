# Nifty 100 Financial Intelligence Platform

**Bluestock Fintech Internship Capstone · Cohort MJ28**  
**Author:** Anusha Sadu · `saduanusha2004`  
**Duration:** 45 calendar days · 6 sprints · Production-grade analytics

---

## Overview

A production-grade financial intelligence system covering all **92 Nifty 100 companies**.  
ETL pipeline → 30+ KPIs → Investment Screener → Peer Comparison → Streamlit Dashboard → Valuation Module.

| Metric | Value |
|--------|-------|
| Companies | 92 Nifty 100 constituents |
| Financial KPIs | 30+ per company |
| Data History | FY 2010–2024 (10–13 years) |
| Screener Filters | 15 configurable metrics |
| Preset Screeners | 6 templates |
| Peer Groups | 11 groups |
| Dashboard Screens | 8 interactive screens |
| Test Coverage | 109 tests, 0 failures |

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/SaduAnusha/n100-financial-intelligence.git
cd n100-financial-intelligence
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add source data files
Place the 7 core Excel files in `data/raw/`:
- `companies.xlsx`, `profitandloss.xlsx`, `balancesheet.xlsx`
- `cashflow.xlsx`, `analysis.xlsx`, `documents.xlsx`, `prosandcons.xlsx`

Place the 5 supplementary files in `data/supporting/`:
- `sectors.xlsx`, `stock_prices.xlsx`, `market_cap.xlsx`
- `financial_ratios.xlsx`, `peer_groups.xlsx`

### 5. Build the database
```bash
python db/loader.py
```

### 6. Run the ratio engine
```bash
python src/analytics/ratio_engine.py
```

### 7. Run the screener export
```bash
python src/screener/export.py
```

### 8. Run the peer comparison engine
```bash
python src/analytics/peer.py
```

### 9. Run the valuation module
```bash
python src/analytics/valuation.py
```

### 10. Launch the Streamlit dashboard
```bash
streamlit run src/dashboard/app.py
```
Open your browser at **http://localhost:8501**

---

## Makefile Shortcuts

```bash
make load       # Build nifty100.db from all 12 source files
make ratios     # Populate financial_ratios table
make test       # Run full test suite (109 tests)
make dashboard  # Launch Streamlit dashboard at localhost:8501
make report     # Generate PDF reports
make api        # Start FastAPI server
make clean      # Clean output files
```

---

## Dashboard Screens

| Screen | URL | Description |
|--------|-----|-------------|
| 🏠 Home | `/home` | Market summary KPIs, sector donut chart, top 10 companies |
| 🏢 Company Profile | `/profile` | Full financial profile, 10yr charts, KPI tiles |
| 🔍 Screener | `/screener` | 15 metric sliders, 6 presets, CSV download |
| 👥 Peer Comparison | `/peers` | Radar chart, percentile rankings across 11 groups |
| 📈 Trend Analysis | `/trends` | 10yr multi-metric overlay with YoY annotations |
| 🏭 Sector Analysis | `/sectors` | Bubble chart, sector median KPI table |
| 💰 Capital Allocation | `/capital` | Treemap of 92 companies by cash flow pattern |
| 📄 Annual Reports | `/reports` | BSE PDF links per company and year |

---

## Project Structure

```
n100-financial-intelligence/
├── data/
│   ├── raw/              # 7 core Excel files (READ ONLY)
│   └── supporting/       # 5 supplementary Excel files
├── db/
│   ├── schema.sql        # 12-table SQLite schema
│   ├── loader.py         # Full ETL loader
│   └── nifty100.db       # SQLite database (generated)
├── src/
│   ├── etl/              # loader.py, normaliser.py, validator.py
│   ├── analytics/        # ratios.py, cagr.py, cashflow_kpis.py,
│   │                     # ratio_engine.py, peer.py, radar_charts.py,
│   │                     # valuation.py
│   ├── screener/         # engine.py, export.py
│   └── dashboard/
│       ├── app.py        # Main Streamlit entry point
│       ├── utils/db.py   # Cached data loader
│       └── pages/        # 8 screen files (01-08)
├── tests/
│   ├── etl/              # 43 normaliser tests
│   └── kpi/              # 66 KPI formula tests
├── output/               # Generated outputs
│   ├── load_audit.csv
│   ├── validation_failures.csv
│   ├── capital_allocation.csv
│   ├── screener_output.xlsx
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx
│   └── valuation_flags.csv
├── reports/
│   └── radar_charts/     # 55 radar chart PNGs
├── notebooks/            # SQL queries, QA review, retrospectives
├── config/
│   └── screener_config.yaml
├── requirements.txt
├── Makefile
└── README.md
```

---

## Sprint Summary

| Sprint | Days | Focus | Key Deliverable |
|--------|------|-------|-----------------|
| Sprint 1 | 1–7 | Data Foundation | `nifty100.db` — 12 tables, 0 FK violations |
| Sprint 2 | 8–14 | Ratio Engine | `financial_ratios` table — 1,041 rows, 30+ KPIs |
| Sprint 3 | 15–21 | Screener & Peers | `screener_output.xlsx`, `peer_comparison.xlsx`, 55 radar charts |
| Sprint 4 | 22–28 | Dashboard & Valuation | 8-screen Streamlit app, `valuation_summary.xlsx` |

---

## Test Results

```
109 passed in 0.95s
```

- `tests/etl/` — 43 tests (year normalisation, ticker normalisation)
- `tests/kpi/` — 66 tests (ratios, CAGR, cash flow patterns)

---

## Known Data Gaps

- **8 companies** (ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VEDL, WIPRO, ZOMATO, ZYDUSLIFE + AGTL) are present in time-series files but missing from `companies.xlsx`. These are excluded from the database per DQ-03 (FK integrity). This reduces the financial_ratios row count from the 1,100 target to 1,041.
- `companies.xlsx` marks 3 columns as non-nullable that have real nulls in the data (`face_value`, `operating_profit`, `opm_percentage`). Schema constraints were relaxed to match reality.

---

## Tech Stack

Python 3.10+ · pandas · numpy · SQLite · openpyxl · Streamlit · Plotly · matplotlib · ReportLab · pytest · PyYAML · python-dotenv
