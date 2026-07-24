# Sprint 2 Retrospective — Financial Ratio Engine

**Project:** N100 Financial Intelligence Platform
**Sprint:** Sprint 2 (Days 8–14) — Financial Ratio Engine
**Date:** 2026-07-07
**Author:** Anusha Sadu

## Sprint Goal (as stated)

> By end of Sprint 2, the Ratio Engine must compute 50+ KPIs for all 92
> companies across all available years. The financial_ratios table in SQLite
> must be fully populated. All formula edge cases must be handled correctly
> and logged. All 20 KPI formula unit tests must pass.

## Exit Criteria — Final Check

| Criterion | Target | Actual | Pass? |
|---|---|---|---|
| `SELECT COUNT(*) FROM financial_ratios` | ≥ 1,100 | 1,041 | Partial — see note |
| All 14 KPI columns populated | Zero null-only columns | All columns populated | Yes |
| All 20 KPI formula unit tests pass | 20 | 109 total, 0 failures | Yes (exceeded) |
| ratio_edge_cases.log exists | All entries explained | 8 ROE anomalies + CAGR + OPM documented | Yes |
| Sprint review signed off | — | Pending PM | Open |

**Note on row count:** The 1,041 rows is the maximum achievable given
the Sprint 1 data gap (8 companies missing from companies.xlsx). The
FK constraint correctly prevents loading ratios for companies not in the
master table. This is a source data issue, not a formula or engine bug.

## What Was Delivered

| Deliverable | Status | Notes |
|---|---|---|
| `src/analytics/ratios.py` | Done | NPM, OPM, ROE, ROCE, ROA, D/E, ICR, Net Debt, Asset Turnover |
| `src/analytics/cagr.py` | Done | Revenue/PAT/EPS CAGR, 3/5/10yr, all 6 edge cases |
| `src/analytics/cashflow_kpis.py` | Done | FCF, CFO quality, CapEx intensity, 8-pattern classifier |
| `src/analytics/ratio_engine.py` | Done | Full engine populating financial_ratios table |
| `output/capital_allocation.csv` | Done | 1,187 rows, all 8 patterns confirmed |
| `output/ratio_edge_cases.log` | Done | 8 ROE anomalies + bank carve-out rules documented |
| `tests/kpi/` | Done | 66 KPI tests (36 ratios + 10 CAGR + 20 cashflow) |

## What Went Well

- Every KPI function is pure and independently testable — made debugging
  straightforward and unit tests fast to write.
- Grounding every formula in real data before coding (checking actual
  edge cases in the Excel files) prevented several bugs that would have
  been harder to find later.
- The TCS ROE anomaly (source = 0.52, computed = 50.94%) was caught
  immediately because we cross-checked against known public values.
- 109 tests passing gives strong confidence the formula layer is solid
  going into Sprint 3 (screener reads from financial_ratios).

## What Didn't Go Well / Open Issues

- **financial_ratios row count (1,041 vs 1,100 target):** The missing-
  companies gap from Sprint 1 carried forward and reduced the achievable
  maximum. Needs resolution at source (companies.xlsx correction) before
  Sprint 3 screener results will cover all 92 companies.
- **Sprint 2 completed after deadline (July 4):** Work finished July 7
  due to the compressed Sprint 1 timeline and Sprint 3 being assigned
  before Sprint 2 was fully closed. Recommend tighter day-by-day tracking
  in Sprint 3 to avoid deadline slippage.
- **CAGR engine is slow on full dataset:** Computing per-company CAGR
  by scanning the full P&L DataFrame for each row is O(n²). Acceptable
  for 92 companies but should be optimised before scaling.

## Action Items for Sprint 3

1. Resolve missing-companies gap before building the screener, since
   screener results will be incomplete for those 8 companies.
2. Use `financial_ratios` table as the backbone for all screener filters
   (it's now populated and queryable).
3. Optimise CAGR computation if Sprint 3 requires re-running the full
   ratio engine frequently.
