-- N100 Financial Intelligence Platform — Exploratory Queries
-- Day 7 deliverable (DAD-PROJ-001 Sprint 1, Day 07)
-- 10 queries covering row counts, nulls, year coverage, and sanity checks
-- across the data loaded into nifty100.db.

-- ===========================================================================
-- Query 1: Row counts for every table (overall load summary)
-- ===========================================================================
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;


-- ===========================================================================
-- Query 2: Year coverage per company in profitandloss (min/max/count)
-- ===========================================================================
SELECT
    company_id,
    COUNT(DISTINCT year) AS years_covered,
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year
FROM profitandloss
GROUP BY company_id
ORDER BY years_covered ASC;


-- ===========================================================================
-- Query 3: Companies with fewer than 5 years of P&L history (DQ-16 check)
-- ===========================================================================
SELECT
    company_id,
    COUNT(DISTINCT year) AS years_covered
FROM profitandloss
GROUP BY company_id
HAVING years_covered < 5
ORDER BY years_covered ASC;


-- ===========================================================================
-- Query 4: Null check across key nullable columns in companies
-- ===========================================================================
SELECT
    COUNT(*) AS total_companies,
    SUM(CASE WHEN book_value IS NULL THEN 1 ELSE 0 END) AS null_book_value,
    SUM(CASE WHEN roce_percentage IS NULL THEN 1 ELSE 0 END) AS null_roce,
    SUM(CASE WHEN roe_percentage IS NULL THEN 1 ELSE 0 END) AS null_roe,
    SUM(CASE WHEN face_value IS NULL THEN 1 ELSE 0 END) AS null_face_value
FROM companies;


-- ===========================================================================
-- Query 5: Sector distribution — companies per broad_sector
-- ===========================================================================
SELECT
    broad_sector,
    COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;


-- ===========================================================================
-- Query 6: Top 10 companies by latest-year net profit
-- ===========================================================================
SELECT
    p.company_id,
    c.company_name,
    p.year,
    p.net_profit
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
WHERE p.year = (SELECT MAX(year) FROM profitandloss WHERE company_id = p.company_id)
ORDER BY p.net_profit DESC
LIMIT 10;


-- ===========================================================================
-- Query 7: Balance sheet integrity spot-check (top 10 worst imbalances)
-- ===========================================================================
SELECT
    company_id,
    year,
    total_assets,
    total_liabilities,
    ROUND(ABS(total_assets - total_liabilities) * 100.0 / total_assets, 4) AS diff_pct
FROM balancesheet
WHERE total_assets != 0
ORDER BY diff_pct DESC
LIMIT 10;


-- ===========================================================================
-- Query 8: Companies present in time-series data but missing from companies
--          table (orphan check — should be 0 after a clean load, but
--          documents the known data gap if run against raw source files)
-- ===========================================================================
SELECT DISTINCT pl.company_id
FROM profitandloss pl
LEFT JOIN companies c ON pl.company_id = c.id
WHERE c.id IS NULL;


-- ===========================================================================
-- Query 9: Stock price coverage — rows per company (should be 60 each:
--          Jan 2020 - Dec 2024 monthly)
-- ===========================================================================
SELECT
    company_id,
    COUNT(*) AS price_rows
FROM stock_prices
GROUP BY company_id
HAVING price_rows != 60
ORDER BY price_rows ASC;


-- ===========================================================================
-- Query 10: Cross-table join — full profile for one company (TCS), joining
--           companies, sectors, and latest financial_ratios
-- ===========================================================================
SELECT
    c.id,
    c.company_name,
    s.broad_sector,
    s.sub_sector,
    fr.year,
    fr.return_on_equity_pct,
    fr.debt_to_equity,
    fr.net_profit_margin_pct
FROM companies c
JOIN sectors s ON c.id = s.company_id
LEFT JOIN financial_ratios fr ON c.id = fr.company_id
    AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
WHERE c.id = 'TCS';
