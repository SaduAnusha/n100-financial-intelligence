"""
Day 36 — src/analytics/clustering.py

KMeans clustering with 5 clusters for all 92 Nifty 100 companies.
Features: ROE, D/E, Revenue CAGR, Profit CAGR, OPM
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "output"
REPORTS_DIR = "reports"

CLUSTER_NAMES = {
    0: "High-Quality Compounders",
    1: "Dividend Defenders",
    2: "Value Cyclicals",
    3: "Growth Leaders",
    4: "Distressed/Turnaround"
}

def load_financial_data():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        fr.company_id, fr.return_on_equity_pct as roe, fr.debt_to_equity as de,
        fr.revenue_cagr_5yr as rev_cagr, fr.pat_cagr_5yr as profit_cagr,
        fr.operating_profit_margin_pct as opm, c.company_name, s.broad_sector
    FROM financial_ratios fr
    JOIN companies c ON fr.company_id = c.id
    JOIN sectors s ON fr.company_id = s.company_id
    WHERE (fr.company_id, fr.year) IN (
        SELECT company_id, MAX(year) FROM financial_ratios GROUP BY company_id
    )
    ORDER BY fr.company_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def impute_sector_median(df):
    df = df.copy()
    features = ['roe', 'de', 'rev_cagr', 'profit_cagr', 'opm']
    for feature in features:
        sector_median_map = df.groupby('broad_sector')[feature].transform('median')
        df[feature] = df[feature].fillna(sector_median_map)
    for feature in features:
        global_median = df[feature].median()
        df[feature] = df[feature].fillna(global_median)
    return df

def run_kmeans_clustering(df):
    features = ['roe', 'de', 'rev_cagr', 'profit_cagr', 'opm']
    X = df[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    distances = kmeans.transform(X_scaled).min(axis=1)
    return clusters, distances, kmeans, scaler, X_scaled

def generate_elbow_plot(df):
    features = ['roe', 'de', 'rev_cagr', 'profit_cagr', 'opm']
    X = df[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    inertias = []
    ks = range(2, 11)
    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(ks, inertias, marker='o', linewidth=2, markersize=8, color='#1565C0')
    ax.axvline(x=5, color='red', linestyle='--', linewidth=2, label='k=5 (selected)')
    ax.set_xlabel('Number of Clusters (k)', fontsize=11)
    ax.set_ylabel('Inertia', fontsize=11)
    ax.set_title('KMeans Elbow Curve', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{REPORTS_DIR}/elbow_plot.png", dpi=150)
    plt.close()
    print(f"✓ Elbow plot saved to {REPORTS_DIR}/elbow_plot.png")

def save_cluster_labels(df, clusters, distances):
    output_df = pd.DataFrame({
        'company_id': df['company_id'].values,
        'company_name': df['company_name'].values,
        'broad_sector': df['broad_sector'].values,
        'cluster_id': clusters,
        'cluster_name': [CLUSTER_NAMES[c] for c in clusters],
        'distance_from_centroid': distances
    })
    output_df = output_df.sort_values('company_id').reset_index(drop=True)
    output_df.to_csv(f"{OUTPUT_DIR}/cluster_labels.csv", index=False)
    print(f"\n✓ Cluster Distribution:\n{output_df['cluster_name'].value_counts()}")
    print(f"\n✓ Cluster labels saved to {OUTPUT_DIR}/cluster_labels.csv")

def main():
    print("Loading financial data...")
    df = load_financial_data()
    print(f"✓ Loaded {len(df)} companies\n")
    print("Imputing missing values...")
    df = impute_sector_median(df)
    print(f"✓ All missing values imputed\n")
    print("Generating elbow plot...")
    generate_elbow_plot(df)
    print("\nRunning KMeans clustering...")
    clusters, distances, kmeans, scaler, X_scaled = run_kmeans_clustering(df)
    print(f"✓ Clustering complete\n")
    print("Saving cluster labels...")
    save_cluster_labels(df, clusters, distances)
    print("\n✅ Day 36 complete!")

if __name__ == "__main__":
    main()
