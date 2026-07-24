# Day 6 — Data Quality Manual Review

**Date:** 2026-06-21
**Reviewer:** Anusha Sadu
**Scope:** Manual spot-check of 5 randomly sampled companies across profitandloss, balancesheet, and cashflow tables, plus a full-database coverage check.

## Sample Selected (random, seed=42)
SUNPHARMA, BAJFINANCE, ADANIGREEN, HAL, EICHERMOT

## Year Coverage Check

| Company    | P&L Records | Year Range          | BS Records | CF Records |
|------------|-------------|----------------------|------------|------------|
| SUNPHARMA  | 12          | 2013-03 to 2024-03   | 13         | 12         |
| BAJFINANCE | 10          | 2015-03 to 2024-03   | 11         | 10         |
| ADANIGREEN | 8           | 2017-03 to 2024-03   | 9          | 8          |
| HAL        | 12          | 2013-03 to 2024-03   | 10         | 8          |
| EICHERMOT  | 12          | 2012-12 to 2024-03   | 13         | 12         |

All 5 sampled companies have >= 8 years of history, well above the DQ-16
minimum of 5 years. No action needed for this sample.

## Database-Wide Coverage Check (DQ-16)

Companies with < 5 years of P&L history: **1** (JIOFIN — 2 years).
This is expected, not a bug: Jio Financial Services is a recently listed
company with genuinely limited historical financial data. Flagged per
DQ-16 but not excluded, since the limited data it does have is legitimate.

All 92 companies present in the `companies` table have at least some
P&L data loaded (no company was loaded with zero records).

## Balance Sheet Sanity Check

Spot-checked the latest available year for each of the 5 sampled
companies: `total_assets` vs `total_liabilities`.

| Company    | Latest Year | Assets   | Liabilities | Diff % |
|------------|-------------|----------|--------------|--------|
| SUNPHARMA  | 2024-09     | 88,116   | 88,116       | 0.000% |
| BAJFINANCE | 2024-09     | 420,656  | 420,656      | 0.000% |
| ADANIGREEN | 2024-09     | 98,258   | 98,258       | 0.000% |
| HAL        | 2024-09     | 476      | 476          | 0.000% |
| EICHERMOT  | 2024-09     | 24,380   | 24,380       | 0.000% |

All balance perfectly. No imbalances found in this sample (consistent
with the validator's earlier finding of 0 DQ-04 violations across the
full dataset).

## P&L Trend Sanity Check (SUNPHARMA, illustrative)

| Year     | Sales  | Operating Profit | OPM % | Net Profit | EPS |
|----------|--------|-------------------|-------|------------|-----|
| 2022-03  | 38,654 | 10,258            | 27%   | 3,389      | 14  |
| 2023-03  | 43,886 | 11,650            | 27%   | 8,513      | 35  |
| 2024-03  | 48,497 | 13,018            | 28%   | 9,610      | 40  |

Growth trajectory is coherent and believable for a large pharma company
— revenue, profit, and EPS all rising together, OPM stable. No anomalies.

## Loader Bugs Found / Fixed

During Day 5 build-out (before this review), 3 schema constraint bugs
were found and fixed:
- `companies.face_value` — relaxed NOT NULL (1 real null: TVSMOTOR)
- `profitandloss.operating_profit` — relaxed NOT NULL (13 real nulls)
- `profitandloss.opm_percentage` — relaxed NOT NULL (15 real nulls)

No additional loader bugs found during this Day 6 manual review. No
re-run of the load was necessary as a result of this review.

## Outstanding Known Issue (carried from Day 3)

8 companies (ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VEDL, WIPRO, ZOMATO,
ZYDUSLIFE) plus AGTL are present in one or more time-series source
files but missing from `companies.xlsx`. These are correctly excluded
from the database per DQ-03 (FK integrity). Flagged to team lead;
awaiting confirmation on whether `companies.xlsx` will be corrected.

## Conclusion

Manual review of 5 random companies plus full-database coverage check
found no data integrity issues beyond what was already documented in
Sprint 1's validation_failures.csv and load_audit.csv. The pipeline is
producing clean, internally consistent data. **No re-run required.**
