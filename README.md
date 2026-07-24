# Nifty 100 Financial Intelligence Platform

**Bluestock Fintech Internship Capstone · Cohort MJ28**
**Author:** Anusha Sadu · saduanusha2004
**Duration:** 45 calendar days · 6 sprints · Production-grade analytics

---

## Overview

Production-grade financial intelligence system for all 92 Nifty 100 companies.
ETL pipeline → 30+ KPIs → Screener → Dashboard → Reports → API Server.

| Metric | Value |
|--------|-------|
| Companies | 92 Nifty 100 constituents |
| Financial KPIs | 30+ per company |
| Dashboard Screens | 8 interactive pages |
| Company Reports | 90 PDF tearsheets ✅ |
| Sector Reports | 10 PDF summaries ✅ |
| Test Coverage | 109 tests, 0 failures |

---

## Quick Start

### 1. Setup
\\\ash
git clone https://github.com/SaduAnusha/n100-financial-intelligence.git
cd n100-financial-intelligence
pip install -r requirements.txt
\\\

### 2. Run Dashboard
\\\ash
python -m streamlit run src/dashboard/app.py
\\\
Open: **http://localhost:8501**

---

## Dashboard Screens

| Screen | Description |
|--------|-------------|
| Home | Market summary, top 10 companies |
| Company Profile | Full financials, 10yr charts |
| Screener | 15 filters, 6 presets |
| Peer Comparison | Radar chart, percentiles |
| Trends | 10yr overlay |
| Sectors | Bubble chart |
| Capital Allocation | Treemap |
| Reports | PDF links |

---

## Sprint Status

| Sprint | Focus | Status |
|--------|-------|--------|
| 1–4 | Data, Ratios, Screener, Dashboard | ✅ Complete |
| **5** | **Dashboard & Reporting** | **✅ COMPLETE** |
| **6** | **API & Clustering** | **🚧 IN PROGRESS** |

---

## Sprint 5 ✅ COMPLETE

**Deliverables:**
- ✅ 90 company tearsheets (PDF)
- ✅ 10 sector reports (PDF)
- ✅ 8-page Streamlit dashboard
- ✅ Portfolio summary

**Files:** 
eports/tearsheets/ (90 PDFs), 
eports/sector/ (10 PDFs)

---

## Sprint 6 🚧 IN PROGRESS

**Timeline: 3 days remaining**

### Phase 1: Clustering
- KMeans (5 clusters)
- output/cluster_labels.csv
- Elbow plot + correlation heatmap

### Phase 2: FastAPI
- 16 REST endpoints
- /companies, /screener, /sectors, /peers, /tearsheet
- OpenAPI docs

### Phase 3: Testing & Sign-Off
- 60+ tests
- 20 acceptance gates

---

## Tech Stack

Python 3.10+ · pandas · SQLite · Streamlit · Plotly · ReportLab · pytest · FastAPI (planned) · scikit-learn (planned)

---

## How to Run

Dashboard:
\\\ash
python -m streamlit run src/dashboard/app.py
\\\

Tests:
\\\ash
pytest tests/ -v
\\\

API (Sprint 6):
\\\ash
uvicorn src.api.main:app --port 8000
\\\

---

## Contact

**GitHub:** github.com/SaduAnusha  
**LinkedIn:** linkedin.com/in/anusha-sadu-1179863ba
