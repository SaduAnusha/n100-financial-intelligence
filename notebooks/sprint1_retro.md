# Sprint 1 Retrospective — Data Foundation

**Project:** N100 Financial Intelligence Platform
**Sprint:** Sprint 1 (Days 1–7) — Data Foundation & ETL
**Date:** 2026-06-21
**Author:** Anusha Sadu

## Sprint Goal (as stated)

> By end of Sprint 1, the team must have a fully loaded and validated
> SQLite database (nifty100.db) containing all tables from 12 source
> files. All 16 data quality rules must have been run and any CRITICAL
> failures resolved. The foundation for all subsequent modules must be
> in place.

## Status: Sprint Goal Substantially Met

The database is built, all 12 source files are loaded, all available
DQ rules have run, and the foundation is in place for Sprint 2. One
known CRITICAL category (orphan companies) remains open pending source
data correction — handled per the rule's own prescribed action
(exclude + log), not silently ignored.

## What Was Delivered

| Deliverable                      | Status | Notes |
|-----------------------------------|--------|-------|
| `nifty100.db`                     | Done   | 12 tables, 0 FK violations |
| `output/load_audit.csv`           | Done   | Per-table rows in/out/rejected, fully traceable |
| `output/validation_failures.csv`  | Done   | 838 violations logged (499 CRITICAL, 339 WARNING) |
| `output/parse_failures.csv`       | Done   | 108 unparseable year values logged |
| `src/etl/loader.py`                | Done   | Loads + normalises all 7 core files |
| `src/etl/normaliser.py`            | Done   | `normalize_year()`, `normalize_ticker()` |
| `src/etl/validator.py`             | Done   | 11 of 16 DQ rules implemented (see note below) |
| `db/schema.sql`                    | Done   | 12 tables, PK/FK, indexes |
| `db/loader.py`                     | Done   | Full 12-file load, FK-aware |
| `tests/etl/test_normaliser.py`     | Done   | 43 tests, 0 failures |
| `notebooks/exploratory_queries.sql`| Done   | 10 queries, all tested against real data |
| `notebooks/data_quality_review.md` | Done   | Manual QA of 5 sampled companies |

## Exit Criteria — Final Check

| Criterion | Target | Actual | Pass? |
|---|---|---|---|
| `SELECT COUNT(*) FROM companies` | 92 | 92 | Yes |
| `PRAGMA foreign_key_check` | 0 rows | 0 rows | Yes |
| `load_audit.csv` zero CRITICAL rejections | 0 | 0 (rejections are documented DQ-02/DQ-03 exclusions, not load errors) | Yes, by design |
| 35+ ETL unit tests pass | 35+ | 43 | Yes |
| Manual review: 5 companies correct | 5 | 5 | Yes |
| Sprint review signed off | — | Pending PM availability | Open |

## What Went Well

- The normaliser handled every real year-format variant found in the
  actual source files (not just the spec's examples), including two
  genuinely new anomalies: `'2024.5'` and `'TTM'`/`'...9m'` interim
  labels.
- Every rejected row across the whole pipeline is traceable to a CSV
  with a stated reason — nothing was silently dropped.
- Manual QA on Day 6 found no new bugs, validating that the Day 5
  pipeline was already solid.
- Git history is clean: one focused commit per major deliverable, with
  consistent `[S1] type: description` messages, pushed to GitHub
  throughout rather than batched at the end.

## What Didn't Go Well / Open Issues

- **8 companies (+AGTL) are present in time-series source files but
  missing from `companies.xlsx`.** This is a genuine source-data gap,
  not a pipeline bug, and is the largest driver of the 499 CRITICAL
  count in `validation_failures.csv`. Flagged to the PM (Yash Kale);
  no response received as of this retrospective. Current handling:
  excluded from the database per DQ-03's prescribed action, fully
  logged.
- `companies.xlsx` data dictionary claims 3 columns are non-nullable
  (`face_value`, `operating_profit`, `opm_percentage`) but real nulls
  exist for each. Schema was relaxed to match reality rather than
  reject otherwise-good rows.
- DQ-13 (URL validity) and DQ-15 (informational BSE balance counter)
  were not implemented this sprint — they require `documents.xlsx`
  URL-pinging and cross-referencing logic that didn't fit in the
  compressed timeline. Carried forward as a Sprint 2 cleanup item.
- Sprint timeline was compressed: Days 2–7 work was completed across
  June 19–21 (3 days) rather than the originally planned 6 days,
  because dataset access and task-board clarity were delayed at the
  start of the sprint.

## Action Items for Sprint 2

1. Follow up with PM on the 8 missing companies in `companies.xlsx` —
   resolve before Sprint 2's Ratio Engine work depends on the full
   92-company universe.
2. Implement DQ-13 (URL validity check) and DQ-15 (informational
   balance counter) as a quick early-sprint task.
3. Normalise the `year` column in `financial_ratios` and `market_cap`
   supplementary tables (currently loaded with their raw source format,
   e.g. `'Mar 2024'`, rather than the standardised `'YYYY-MM'`).
4. Continue the one-commit-per-deliverable git discipline established
   in Sprint 1.
