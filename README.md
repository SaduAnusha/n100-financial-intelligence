# Nifty 100 Financial Intelligence Platform

**Bluestock Fintech Internship Capstone · Cohort MJ28**
**Author:** Anusha Sadu · `saduanusha2004`
**Duration:** 45 calendar days · 6 sprints · Production-grade analytics

---

## Overview

A production-grade financial intelligence system covering all **92 Nifty 100 companies**.
ETL pipeline → 30+ KPIs → Investment Screener → Peer Comparison → Streamlit Dashboard → Valuation Module → API Server.

| Metric | Value |
|--------|-------|
| Companies | 92 Nifty 100 constituents |
| Financial KPIs | 30+ per company |
| Data History | FY 2010–2024 (10–13 years) |
| Screener Filters | 15 configurable metrics |
| Preset Screeners | 6 templates |
| Peer Groups | 11 groups |
| Dashboard Screens | 8 interactive pages |
| Company Reports | 90 PDF tearsheets (5 pages each) |
| Sector Reports | 10 PDF sector summaries |
| Portfolio Summary | 1 PDF |
| Cluster Archetypes | 5 (90 companies assigned) |
| Test Coverage | 109 tests, 0 failures |

---

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/SaduAnusha/n100-financial-intelligence.git
cd n100-financial-intelligence
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Run Dashboard
```bash
python -m streamlit run src/dashboard/app.py
```
Open your browser at: **http://localhost:8501**

### 3. Run API Server
```bash
python src/api/main.py
```
API docs available at: **http://localhost:8000/docs**

### 4. Run Tests
```bash
pytest tests/ -v
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
│   └── nifty100.db       # SQLite database (1.6 MB, fully loaded)
├── src/
│   ├── etl/              # loader.py, normaliser.py, validator.py
│   ├── analytics/        # ratios.py, cagr.py, cashflow_kpis.py,
│   │                     # peer.py, radar_charts.py, valuation.py,
│   │                     # clustering.py ✅
│   ├── screener/         # engine.py, export.py
│   ├── dashboard/        # Streamlit app (8 pages, 100% working)
│   │   ├── app.py        # Main entry point
│   │   ├── utils/db.py   # Cached data loader
│   │   └── pages/        # 8 screen files (01-08)
│   └── api/              # FastAPI server ✅
│       └── main.py       # 16 REST endpoints
├── tests/
│   ├── etl/              # 43 normaliser tests
│   ├── kpi/              # 66 KPI formula tests
│   └── api/              # Integration tests
├── output/               # Generated outputs
│   ├── load_audit.csv
│   ├── validation_failures.csv
│   ├── screener_output.xlsx
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx
│   ├── capital_allocation.csv
│   ├── cluster_labels.csv ✅
│   └── outlier_report.csv
├── reports/
│   ├── tearsheets/       # 90 company PDFs
│   ├── sector/           # 10 sector reports
│   ├── portfolio/        # 1 portfolio summary
│   ├── radar_charts/     # 92 radar chart PNGs
│   └── elbow_plot.png ✅
├── docs/
│   ├── analyst_guide.pdf ✅
│   ├── acceptance_checklist.pdf ✅
│   └── DELIVERY_SUMMARY.txt
├── notebooks/            # SQL queries, QA review, retrospectives
├── config/
│   └── screener_config.yaml
├── requirements.txt
├── README.md
└── Makefile
```

---

## Sprint Summary

| Sprint | Days | Focus | Status |
|--------|------|-------|--------|
| Sprint 1 | 1–7 | Data Foundation | ✅ **COMPLETE** |
| Sprint 2 | 8–14 | Ratio Engine | ✅ **COMPLETE** |
| Sprint 3 | 15–21 | Screener & Peers | ✅ **COMPLETE** |
| Sprint 4 | 22–28 | Dashboard & Valuation | ✅ **COMPLETE** |
| **Sprint 5** | **29–35** | **Dashboard & Reporting** | **✅ COMPLETE** |
| **Sprint 6** | **36–45** | **API & Clustering** | **✅ COMPLETE** |

---

## Sprint 5 — Dashboard & Reporting ✅ COMPLETE

**What was delivered:**
- ✅ 8-page Streamlit dashboard (all pages fully functional)
- ✅ 90 company tearsheets (PDF, 5 pages each, with KPIs, charts, pros/cons)
- ✅ 10 sector reports (PDF summaries per sector)
- ✅ 1 portfolio summary (PDF market-level aggregations)

**Files generated:**
- `reports/tearsheets/` — 90 PDFs (ABB_tearsheet.pdf → TVSMOTOR_tearsheet.pdf)
- `reports/sector/` — 10 PDFs (Communication_Services_report.pdf → Information_Technology_report.pdf)
- `reports/portfolio/portfolio_summary.pdf`
- `reports/radar_charts/` — 92 PNG radar charts

**Run the dashboard:**
```bash
python -m streamlit run src/dashboard/app.py
# Loads at http://localhost:8501
# All 8 pages working: Home, Profile, Screener, Peers, Trends, Sectors, Capital, Reports
```

---

## Sprint 6 — API & Clustering ✅ COMPLETE

### Phase 1: Clustering (Days 36–37) ✅ COMPLETE
- ✅ `src/analytics/clustering.py` — KMeans with 5 clusters using 5 financial metrics
- ✅ `reports/elbow_plot.png` — Elbow curve confirming k=5
- ✅ `output/cluster_labels.csv` — All 90 companies with cluster ID + name

### Phase 2: FastAPI Server (Days 38–40) ✅ COMPLETE
- ✅ `src/api/main.py` — FastAPI app with 16 endpoints

**16 Endpoints:**
- Companies: `/companies`, `/companies/{ticker}`, `/companies/{ticker}/pl`, `/companies/{ticker}/bs`, `/companies/{ticker}/cashflow`, `/companies/{ticker}/ratios`
- Screener: `/screener` (with filters)
- Sectors: `/sectors`, `/sectors/{sector}/companies`
- Peers: `/peers/{group_name}`, `/companies/{ticker}/peers/compare`
- Valuation: `/market-cap/{ticker}`
- Portfolio: `/portfolio/stats`
- Clustering: `/clusters`
- Health: `/health` (status check)

**Run the API:**
```bash
python src/api/main.py
# Runs at http://localhost:8000
# OpenAPI docs: http://localhost:8000/docs
```

### Phase 3: Testing & Sign-Off (Days 41–45) ✅ COMPLETE
- ✅ 109 tests (43 ETL + 66 KPI)
- ✅ `reports/pytest_report.html` — Test report
- ✅ `docs/analyst_guide.pdf` — 10+ page user guide
- ✅ `docs/acceptance_checklist.pdf` — 20 acceptance gates verified

---

## Test Results

```
109 passed in 1.81s
```

- `tests/etl/` — 43 tests (normaliser, loader)
- `tests/kpi/` — 66 tests (ratios, CAGR, cash flow patterns)

**All tests passing. Zero failures.**

---

## API Endpoints (16 Total)

### Health & Info
- `GET /` — API info
- `GET /api/v1/health` — Database health check

### Companies (6 endpoints)
- `GET /api/v1/companies` — List all 92 companies
- `GET /api/v1/companies/{ticker}` — Full company profile
- `GET /api/v1/companies/{ticker}/pl` — P&L history
- `GET /api/v1/companies/{ticker}/bs` — Balance sheet history
- `GET /api/v1/companies/{ticker}/cashflow` — Cash flow history
- `GET /api/v1/companies/{ticker}/ratios` — All KPIs

### Screener & Analytics (4 endpoints)
- `GET /api/v1/screener` — Filtered search
- `GET /api/v1/sectors` — All 11 sectors
- `GET /api/v1/sectors/{sector}/companies` — Companies in sector
- `GET /api/v1/peers/{group_name}` — Peer group data

### Valuation & Portfolio (3 endpoints)
- `GET /api/v1/market-cap/{ticker}` — Valuation multiples
- `GET /api/v1/portfolio/stats` — Market-level statistics
- `GET /api/v1/companies/{ticker}/peers/compare` — Peer comparison

### Clustering (1 endpoint)
- `GET /api/clusters` — Cluster assignments (5 archetypes)

---

## Cluster Archetypes (5 Total)

| Cluster | Companies | Profile |
|---------|-----------|---------|
| **High-Quality Compounders** | 6 | Strong ROE, low D/E, high CAGR, stable margins |
| **Dividend Defenders** | 14 | Stable, predictable, high dividend payout |
| **Value Cyclicals** | 56 | Moderate metrics, cyclical by nature |
| **Growth Leaders** | 2 | High growth, emerging, lower profitability |
| **Distressed/Turnaround** | 12 | Weak metrics, recovery plays |

---

## Known Data Gaps

- **2 companies skipped** in tearsheet generation:
  - ATGL — no cash flow data available
  - SBIN — fewer than 3 years of balance sheet data

These are logged in `output/skipped_tearsheets.csv`

---

## Tech Stack

- **Language:** Python 3.10+
- **Data:** pandas, numpy, SQLite, openpyxl
- **Dashboard:** Streamlit, Plotly, matplotlib
- **Reports:** ReportLab (PDFs)
- **API:** FastAPI, Uvicorn
- **ML:** scikit-learn (KMeans clustering)
- **Testing:** pytest
- **Config:** PyYAML, python-dotenv

---

## How to Run Everything

### Dashboard
```bash
python -m streamlit run src/dashboard/app.py
# http://localhost:8501
```

### API Server
```bash
python src/api/main.py
# http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Generate Reports (if needed)
```bash
python src/reports/tearsheet.py        # Company tearsheets
python src/reports/sector_report.py    # Sector reports
python src/reports/portfolio_summary.py # Portfolio summary
```

### Run Clustering
```bash
python src/analytics/clustering.py
# Outputs: output/cluster_labels.csv, reports/elbow_plot.png
```

### Run Tests
```bash
pytest tests/ -v
# 109 passed
```

### Build Database from Scratch (optional)
```bash
# Database is pre-built (db/nifty100.db)
# To rebuild from source Excel files:
python db/loader.py
python src/analytics/ratio_engine.py
python src/screener/export.py
python src/analytics/peer.py
python src/analytics/valuation.py
python src/analytics/clustering.py
```

---

## Deliverables Checklist (23/23)

✅ D-01 to D-19: Sprints 1-5 (Database, KPIs, Screener, Dashboard, Reports)
✅ D-20: FastAPI Server (16 endpoints)
✅ D-21: pytest_report.html (109 tests, 0 failures)
✅ D-22: analyst_guide.pdf (10+ pages)
✅ D-23: acceptance_checklist.pdf (20 gates verified)

---

## Acceptance Gates (20/20 Verified)

| Gate | Requirement | Status |
|------|-------------|--------|
| AC-01 | 92 companies in database | ✅ PASS |
| AC-02 | 90%+ have 10yr data | ✅ PASS |
| AC-03 | 0 FK violations | ✅ PASS |
| AC-04 | 1,000+ KPI rows | ✅ PASS |
| AC-05 | CAGR accuracy | ✅ PASS |
| AC-06 | ROE validation | ✅ PASS |
| AC-07 | Screener preset | ✅ PASS |
| AC-08 | Dashboard load time | ✅ PASS |
| AC-09 | CSV export valid | ✅ PASS |
| AC-10 | PDF tearsheets | ✅ PASS |
| AC-11 | Dashboard running | ✅ PASS |
| AC-12 | Company history | ✅ PASS |
| AC-13 | Screener consistency | ✅ PASS |
| AC-14 | Peer groups | ✅ PASS |
| AC-15 | Clustering complete | ✅ PASS |
| AC-16 | Pros/cons coverage | ✅ PASS |
| AC-17 | Report generation | ✅ PASS |
| AC-18 | Test coverage | ✅ PASS |
| AC-19 | Data quality log | ✅ PASS |
| AC-20 | Elbow plot | ✅ PASS |

---

## Contact & Support

**Author:** Anusha Sadu  
**GitHub:** github.com/SaduAnusha  
**LinkedIn:** linkedin.com/in/anusha-sadu-1179863ba  
**Email:** saduanusha2004@gmail.com

---

## Changelog

- **2026-07-23, 11:53 AM** — Sprint 5 complete: 90/92 company tearsheets + 10 sector reports generated
- **2026-07-23, 22:14** — Dashboard pushed to GitHub with all 8 pages working
- **2026-07-24, 18:14** — Sprint 5 verified: dashboard running at localhost:8501
- **2026-07-25, 17:28** — Sprint 6 Phase 1 complete: KMeans clustering (5 archetypes, 90 companies)
- **2026-07-25, 22:55** — Sprint 6 complete: FastAPI server, tests, documentation, acceptance sign-off
- **2026-07-25, 23:00** — Final README update: ALL 23 DELIVERABLES COMPLETE ✅

---

**PROJECT STATUS: ✅ PRODUCTION-READY**

All deliverables complete. All tests passing. All documentation finalized. Ready for deployment.
