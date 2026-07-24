# Sprint 5 Retrospective — Dashboard & Reporting (Days 29-35)

## Timeline
Compressed from 7 days to ~4 due to deadline pressure (target: July 21).
Completed July 23 (2 days late) after data-transfer issues delayed access
to the real database.

## What shipped
- `src/nlp/parser.py` — parses the `analysis` table's period-text CAGR
  figures. Covers 4 companies (HDFCBANK, INFY, SBILIFE, TCS) because the
  source `analysis.xlsx` only contains records for those 4 — confirmed
  against the raw file, not a parsing bug.
- `src/nlp/pros_cons_generator.py` — rule-based pros/cons for all 92
  companies, built primarily on the real `financial_ratios` table (90
  companies), with genuine reported text merged in for the 4 companies
  that have it, and a minimal fallback (ROE/ROCE only) for the 2 companies
  absent from financial_ratios (ATGL, SBIN).
- `src/analytics/cashflow_intelligence.py` — CFO/CapEx/distress analysis
  for 91 companies (real cashflow + balancesheet tables). 19 companies
  flagged distress.
- `src/reports/tearsheet.py` — 90 two-page company tearsheets (all >=30KB,
  no overflow). 2 companies skipped and logged (ATGL: no cash flow data;
  SBIN: <3 years balance sheet history).
- `src/reports/sector_report.py` — 10 sector PDFs (not 11 — the real
  `sectors` table only has 10 broad sectors; original spec's assumption
  of 11 didn't match the actual taxonomy).
- `src/reports/portfolio_summary.py` — 92-page portfolio summary,
  alphabetical by ticker, 6 KPIs each with trend arrows vs. prior year.

## Key issues encountered
1. **Data transfer failures.** Folder uploads (browser can't zip
   directories) came through empty twice before a proper zip worked.
   Cost significant time.
2. **Fabricated data risk.** Early Sprint 5 work was built against
   synthetic placeholder data before the real DB was available, and
   accidentally got mixed into the real project's `output/` folder.
   Caught before submission — flagged explicitly to avoid submitting
   fake numbers as real analysis.
3. **Source data gaps, not bugs:**
   - `analysis`/`prosandcons` tables: only 4/92 companies have any data
     (source file limitation from Sprint 1 ETL).
   - `financial_ratios`: 90/92 companies (ATGL, SBIN absent).
   - `cashflow`/`balancesheet`: 91/92 companies (ATGL absent from
     cashflow; SBIN has <3 years balance sheet history).
   - Real sector taxonomy: 10 sectors, not the assumed 11.
4. **Date format inconsistency** between tables (`cashflow`/`balancesheet`
   use `YYYY-MM`; `financial_ratios` uses `Mon YYYY`) required separate
   parsing logic per table.

## Exit criteria status
- [x] pros_cons_generated.csv has >=1 pro and >=1 con for all 92 companies
- [x] Tearsheets exist for all non-skipped companies (90/92), all >=30KB
- [x] Visual review of 5 tearsheets: no overflow, no blank pages
- [x] cashflow_intelligence.xlsx has all required columns (91 rows, not 92,
      due to real data gap)
- [ ] Sprint review sign-off by team lead — pending
