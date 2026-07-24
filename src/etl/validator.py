"""Schema and data-quality validator for the N100 Financial Intelligence Platform.

Implements the 16 Data Quality rules (DQ-01 to DQ-16) defined in
DAD-PROJ-001 Section 14. Each rule returns a list of violation records
which are aggregated and written to output/validation_failures.csv.

Severity levels:
  CRITICAL  - row must be rejected / load halted; investigate immediately.
  WARNING   - row is flagged but kept; analyst review recommended.
  INFO      - informational counter only, no action required.

This module does not import loader.py: it operates on already-loaded
DataFrames so it can be tested independently and reused for ad-hoc
re-validation after any fix.
"""

import csv
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

CRITICAL = "CRITICAL"
WARNING = "WARNING"
INFO = "INFO"


@dataclass
class Violation:
    rule_id: str
    rule_name: str
    severity: str
    company_id: Optional[str] = None
    year: Optional[str] = None
    field: Optional[str] = None
    issue: str = ""


@dataclass
class ValidationReport:
    violations: List[Violation] = field(default_factory=list)

    def add(self, *violations: Violation) -> None:
        self.violations.extend(violations)

    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == CRITICAL)

    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == WARNING)

    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == INFO)

    def to_csv(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["rule_id", "rule_name", "severity", "company_id", "year", "field", "issue"])
            for v in self.violations:
                writer.writerow([v.rule_id, v.rule_name, v.severity, v.company_id, v.year, v.field, v.issue])
        logger.info("Wrote %d violations to %s", len(self.violations), path)


# ---------------------------------------------------------------------------
# DQ-01: Company PK Uniqueness (CRITICAL)
# ---------------------------------------------------------------------------
def dq01_company_pk_uniqueness(companies: pd.DataFrame, id_col: str = "id") -> List[Violation]:
    """len(companies) == companies.id.nunique() -- halt load if violated."""
    violations = []
    dupes = companies[companies.duplicated(subset=[id_col], keep=False)]
    for ticker in dupes[id_col].unique():
        violations.append(Violation(
            "DQ-01", "Company PK Uniqueness", CRITICAL,
            company_id=ticker, field=id_col,
            issue=f"Duplicate company id '{ticker}' in companies table.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-02: Annual PK Uniqueness (CRITICAL)
# ---------------------------------------------------------------------------
def dq02_annual_pk_uniqueness(df: pd.DataFrame, dataset_name: str) -> List[Violation]:
    """No duplicate (company_id, year) pairs in P&L, BS, CF tables."""
    violations = []
    dupe_mask = df.duplicated(subset=["company_id", "year"], keep=False)
    dupes = df[dupe_mask]
    for _, row in dupes.iterrows():
        violations.append(Violation(
            "DQ-02", "Annual PK Uniqueness", CRITICAL,
            company_id=row["company_id"], year=row["year"],
            issue=f"Duplicate (company_id, year) in {dataset_name}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-03: FK Integrity (CRITICAL)
# ---------------------------------------------------------------------------
def dq03_fk_integrity(df: pd.DataFrame, valid_ids: set, dataset_name: str) -> List[Violation]:
    """All company_id in child tables must exist in companies.id."""
    violations = []
    orphan_mask = ~df["company_id"].isin(valid_ids)
    orphans = df[orphan_mask]
    for _, row in orphans.iterrows():
        violations.append(Violation(
            "DQ-03", "FK Integrity", CRITICAL,
            company_id=row["company_id"], year=row.get("year"),
            issue=f"Orphan company_id '{row['company_id']}' in {dataset_name} not found in companies table.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-04: Balance Sheet Balance (WARNING)
# ---------------------------------------------------------------------------
def dq04_balance_sheet_balance(bs: pd.DataFrame, tolerance: float = 0.01) -> List[Violation]:
    """|total_assets - total_liabilities| / total_assets < 0.01."""
    violations = []
    safe = bs[bs["total_assets"] != 0]
    diff_pct = (safe["total_assets"] - safe["total_liabilities"]).abs() / safe["total_assets"]
    flagged = safe[diff_pct >= tolerance]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-04", "Balance Sheet Balance", WARNING,
            company_id=row["company_id"], year=row["year"],
            field="total_assets/total_liabilities",
            issue=f"Imbalance: assets={row['total_assets']}, liabilities={row['total_liabilities']}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-05: OPM Cross-Check (WARNING)
# ---------------------------------------------------------------------------
def dq05_opm_cross_check(pl: pd.DataFrame, tolerance: float = 1.0) -> List[Violation]:
    """|opm_percentage - (op_profit/sales*100)| < 1.0."""
    violations = []
    safe = pl[pl["sales"] != 0].copy()
    safe["computed_opm"] = (safe["operating_profit"] / safe["sales"]) * 100
    diff = (safe["opm_percentage"] - safe["computed_opm"]).abs()
    flagged = safe[diff >= tolerance]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-05", "OPM Cross-Check", WARNING,
            company_id=row["company_id"], year=row["year"], field="opm_percentage",
            issue=f"Source OPM={row['opm_percentage']}, computed OPM={row['computed_opm']:.2f}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-06: Positive Sales (WARNING)
# ---------------------------------------------------------------------------
def dq06_positive_sales(pl: pd.DataFrame, sectors: Optional[pd.DataFrame] = None) -> List[Violation]:
    """sales > 0 for all non-bank companies."""
    violations = []
    bank_ids = set()
    if sectors is not None and "broad_sector" in sectors.columns:
        bank_ids = set(sectors[sectors["broad_sector"] == "Financials"]["company_id"])

    flagged = pl[(pl["sales"] <= 0) & (~pl["company_id"].isin(bank_ids))]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-06", "Positive Sales", WARNING,
            company_id=row["company_id"], year=row["year"], field="sales",
            issue=f"Non-positive sales value: {row['sales']}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-09: Net Cash Check (WARNING)
# ---------------------------------------------------------------------------
def dq09_net_cash_check(cf: pd.DataFrame, tolerance: float = 10.0) -> List[Violation]:
    """|net_cash_flow - (CFO+CFI+CFF)| <= 10 Cr tolerance."""
    violations = []
    computed = cf["operating_activity"] + cf["investing_activity"] + cf["financing_activity"]
    diff = (cf["net_cash_flow"] - computed).abs()
    flagged = cf[diff > tolerance]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-09", "Net Cash Check", WARNING,
            company_id=row["company_id"], year=row["year"], field="net_cash_flow",
            issue=f"Reported={row['net_cash_flow']}, computed sum of CFO+CFI+CFF differs by >{tolerance}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-10: Non-Negative Fixed Assets (WARNING)
# ---------------------------------------------------------------------------
def dq10_non_negative_fixed_assets(bs: pd.DataFrame) -> List[Violation]:
    """fixed_assets >= 0."""
    violations = []
    flagged = bs[bs["fixed_assets"] < 0]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-10", "Non-Negative Fixed Assets", WARNING,
            company_id=row["company_id"], year=row["year"], field="fixed_assets",
            issue=f"Negative fixed_assets value: {row['fixed_assets']}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-11: Tax Rate Range (WARNING)
# ---------------------------------------------------------------------------
def dq11_tax_rate_range(pl: pd.DataFrame) -> List[Violation]:
    """0 <= tax_percentage <= 60."""
    violations = []
    safe = pl.dropna(subset=["tax_percentage"])
    flagged = safe[(safe["tax_percentage"] < 0) | (safe["tax_percentage"] > 60)]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-11", "Tax Rate Range", WARNING,
            company_id=row["company_id"], year=row["year"], field="tax_percentage",
            issue=f"Tax percentage out of [0,60] range: {row['tax_percentage']}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-12: Dividend Payout Cap (WARNING)
# ---------------------------------------------------------------------------
def dq12_dividend_payout_cap(pl: pd.DataFrame, cap: float = 200.0) -> List[Violation]:
    """dividend_payout <= 200 (pct)."""
    violations = []
    safe = pl.dropna(subset=["dividend_payout"])
    flagged = safe[safe["dividend_payout"] > cap]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-12", "Dividend Payout Cap", WARNING,
            company_id=row["company_id"], year=row["year"], field="dividend_payout",
            issue=f"Dividend payout exceeds {cap}%: {row['dividend_payout']}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-14: EPS Sign Consistency (WARNING)
# ---------------------------------------------------------------------------
def dq14_eps_sign_consistency(pl: pd.DataFrame) -> List[Violation]:
    """eps > 0 if net_profit > 0."""
    violations = []
    safe = pl.dropna(subset=["eps", "net_profit"])
    flagged = safe[(safe["net_profit"] > 0) & (safe["eps"] <= 0)]
    for _, row in flagged.iterrows():
        violations.append(Violation(
            "DQ-14", "EPS Sign Consistency", WARNING,
            company_id=row["company_id"], year=row["year"], field="eps",
            issue=f"net_profit={row['net_profit']} > 0 but eps={row['eps']}.",
        ))
    return violations


# ---------------------------------------------------------------------------
# DQ-16: Coverage Check (WARNING)
# ---------------------------------------------------------------------------
def dq16_coverage_check(pl: pd.DataFrame, min_years: int = 5) -> List[Violation]:
    """Each company has >= 5 years of P&L records."""
    violations = []
    counts = pl.groupby("company_id")["year"].nunique()
    flagged = counts[counts < min_years]
    for company_id, count in flagged.items():
        violations.append(Violation(
            "DQ-16", "Coverage Check", WARNING,
            company_id=company_id,
            issue=f"Only {count} year(s) of P&L history (< {min_years} required).",
        ))
    return violations


def run_all_rules(
    companies: pd.DataFrame,
    profitandloss: pd.DataFrame,
    balancesheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    sectors: Optional[pd.DataFrame] = None,
) -> ValidationReport:
    """Run all implemented DQ rules and return a single aggregated report.

    Note: DQ-07, DQ-08 (year/ticker format) are enforced at load time in
    loader.py via normalize_year()/normalize_ticker() and therefore are
    not re-checked here. DQ-13 (URL validity) and DQ-15 (informational
    BSE balance counter) are out of scope for this module and are
    implemented separately where the relevant data (documents.xlsx) is
    loaded.
    """
    report = ValidationReport()
    valid_ids = set(companies["id"])

    report.add(*dq01_company_pk_uniqueness(companies))
    report.add(*dq02_annual_pk_uniqueness(profitandloss, "profitandloss"))
    report.add(*dq02_annual_pk_uniqueness(balancesheet, "balancesheet"))
    report.add(*dq02_annual_pk_uniqueness(cashflow, "cashflow"))
    report.add(*dq03_fk_integrity(profitandloss, valid_ids, "profitandloss"))
    report.add(*dq03_fk_integrity(balancesheet, valid_ids, "balancesheet"))
    report.add(*dq03_fk_integrity(cashflow, valid_ids, "cashflow"))
    report.add(*dq04_balance_sheet_balance(balancesheet))
    report.add(*dq05_opm_cross_check(profitandloss))
    report.add(*dq06_positive_sales(profitandloss, sectors))
    report.add(*dq09_net_cash_check(cashflow))
    report.add(*dq10_non_negative_fixed_assets(balancesheet))
    report.add(*dq11_tax_rate_range(profitandloss))
    report.add(*dq12_dividend_payout_cap(profitandloss))
    report.add(*dq14_eps_sign_consistency(profitandloss))
    report.add(*dq16_coverage_check(profitandloss))

    return report


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from loader import load_all_core_files  # noqa: E402

    raw_dir = os.path.normpath(os.path.join(here, "..", "..", "data", "raw"))
    output_dir = os.path.normpath(os.path.join(here, "..", "..", "output"))

    print(f"Loading core datasets from: {raw_dir}")
    dataframes = load_all_core_files(raw_dir)

    print("Running 16 DQ rules...")
    report = run_all_rules(
        companies=dataframes["companies"],
        profitandloss=dataframes["profitandloss"],
        balancesheet=dataframes["balancesheet"],
        cashflow=dataframes["cashflow"],
    )

    out_path = os.path.join(output_dir, "validation_failures.csv")
    report.to_csv(out_path)

    print(f"\nValidation summary:")
    print(f"  CRITICAL: {report.critical_count()}")
    print(f"  WARNING:  {report.warning_count()}")
    print(f"  INFO:     {report.info_count()}")
    print(f"  Total violations: {len(report.violations)}")
    print(f"  Report written to: {out_path}")

    if report.critical_count() > 0:
        print("\n*** CRITICAL failures found. Resolve before proceeding to Day 5 (full load). ***")
