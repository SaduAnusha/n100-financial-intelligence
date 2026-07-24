"""Radar Chart Generator — Day 19 deliverable.

DAD-PROJ-001 Sprint 3.

Generates one radar/polar PNG per company in a peer group, showing:
  - Company values as a filled polygon
  - Peer group average as a dashed outline overlay

8 axes: ROE, NPM, D/E (inv), FCF, Asset Turnover, EPS, Dividend Yield, Market Cap

Output: reports/radar_charts/<TICKER>_radar.png
"""

import logging
import os
import sys

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file output
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

logger = logging.getLogger(__name__)

SUPPORTING_DIR = os.path.join(PROJECT_ROOT, "data", "supporting")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "reports", "radar_charts")

# 8 axes for radar chart
RADAR_METRICS = [
    "return_on_equity_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "asset_turnover",
    "earnings_per_share",
    "dividend_yield_pct",
    "market_cap_crore",
]

RADAR_LABELS = [
    "ROE %", "NPM %", "D/E (inv)",
    "FCF (Cr)", "Asset T/O",
    "EPS", "Div Yield %", "Mkt Cap (Cr)"
]

INVERSE_METRICS = {"debt_to_equity"}  # lower = better, invert for display


def normalise_for_radar(group_df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    """Normalise all metric columns to 0-1 scale within the peer group."""
    result = group_df.copy()
    for metric in metrics:
        if metric not in result.columns:
            result[metric + "_norm"] = 0.5
            continue
        series = result[metric].fillna(0)
        if metric in INVERSE_METRICS:
            series = 1 / (series + 0.01)  # invert D/E
        rng = series.max() - series.min()
        if rng == 0:
            result[metric + "_norm"] = 0.5
        else:
            result[metric + "_norm"] = (series - series.min()) / rng
    return result


def draw_radar(
    ax, values: list, color: str, label: str,
    fill: bool = True, linestyle: str = "-"
) -> None:
    """Draw a single radar polygon on the given axes."""
    n = len(values)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    if fill:
        ax.fill(angles_closed, values_closed, alpha=0.25, color=color)
    ax.plot(angles_closed, values_closed, color=color,
            linewidth=2, linestyle=linestyle, label=label)


def generate_radar_chart(
    company_id: str,
    company_name: str,
    company_values: list,
    group_avg_values: list,
    group_name: str,
    output_path: str,
) -> None:
    """Generate and save a radar chart PNG for one company."""
    n = len(RADAR_LABELS)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.set_facecolor("#F8F9FA")
    fig.patch.set_facecolor("#FFFFFF")

    # Draw grid
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color="grey")
    ax.set_xticks(angles)
    ax.set_xticklabels(RADAR_LABELS, fontsize=9, fontweight="bold")
    ax.grid(color="grey", linestyle="--", linewidth=0.5, alpha=0.5)

    # Plot peer group average (dashed)
    draw_radar(ax, group_avg_values, color="#95A5A6",
               label=f"{group_name} Avg", fill=False, linestyle="--")

    # Plot company (filled)
    draw_radar(ax, company_values, color="#2E86AB",
               label=company_id, fill=True, linestyle="-")

    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=9)
    ax.set_title(
        f"{company_name}\n{group_name} Peer Group",
        size=11, fontweight="bold", pad=20, color="#1F4E79"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)


def generate_all_radar_charts() -> int:
    """Generate radar charts for all companies in all peer groups."""
    pg = pd.read_excel(os.path.join(SUPPORTING_DIR, "peer_groups.xlsx"), header=0)
    pg["company_id"] = pg["company_id"].astype(str).str.strip().str.upper()

    fr = pd.read_excel(os.path.join(SUPPORTING_DIR, "financial_ratios.xlsx"), header=0)
    fr["company_id"] = fr["company_id"].astype(str).str.strip().str.upper()
    fr = fr.sort_values("year").groupby("company_id").last().reset_index()

    mc = pd.read_excel(os.path.join(SUPPORTING_DIR, "market_cap.xlsx"), header=0)
    mc["company_id"] = mc["company_id"].astype(str).str.strip().str.upper()
    mc = mc.sort_values("year").groupby("company_id").last().reset_index()
    mc = mc[["company_id", "market_cap_crore", "dividend_yield_pct"]]

    companies = pd.read_excel(
        os.path.join(PROJECT_ROOT, "data", "raw", "companies.xlsx"), header=1
    )
    companies["id"] = companies["id"].astype(str).str.strip().str.upper()
    name_map = dict(zip(companies["id"], companies["company_name"]))

    data = fr.merge(mc, on="company_id", how="left", suffixes=("", "_mc"))

    charts_generated = 0

    for group_name in pg["peer_group_name"].unique():
        member_ids = pg[pg["peer_group_name"] == group_name]["company_id"].tolist()
        group_data = data[data["company_id"].isin(member_ids)].copy()

        if group_data.empty:
            continue

        # Normalise within group
        group_norm = normalise_for_radar(group_data, RADAR_METRICS)
        norm_cols = [m + "_norm" for m in RADAR_METRICS]

        # Group average
        group_avg = group_norm[norm_cols].mean().tolist()

        for _, row in group_norm.iterrows():
            company_id = row["company_id"]
            company_name = name_map.get(company_id, company_id)
            company_values = [row.get(m, 0.5) for m in norm_cols]

            output_path = os.path.join(OUTPUT_DIR, f"{company_id}_radar.png")
            generate_radar_chart(
                company_id=company_id,
                company_name=company_name,
                company_values=company_values,
                group_avg_values=group_avg,
                group_name=group_name,
                output_path=output_path,
            )
            charts_generated += 1
            logger.info("Generated radar chart: %s", output_path)

    return charts_generated


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    print("Generating radar charts...")
    count = generate_all_radar_charts()
    print(f"Done — {count} radar charts saved to {OUTPUT_DIR}")
