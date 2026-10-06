"""
RetailIQ — Exploratory Data Analysis (EDA)
==========================================
Loads the generated CSV data and produces summary statistics,
distributions, and correlation insights using Pandas and Seaborn.

Output:  outputs/eda/  (PNG charts + summary_stats.csv)

Usage:
    python python/01_eda.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Config ────────────────────────────────────────────────────────────────────
OUT_DIR = "outputs/eda"
os.makedirs(OUT_DIR, exist_ok=True)

PALETTE   = "Blues_d"
FIG_SIZE  = (12, 6)
DPI       = 150
STYLE     = "whitegrid"

sns.set_theme(style=STYLE, palette="muted")
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titlesize": 14})


# ── Load data ─────────────────────────────────────────────────────────────────
def load_data():
    print("Loading data...")
    txn  = pd.read_csv("data/raw/transactions.csv",  parse_dates=["transaction_date"])
    prod = pd.read_csv("data/raw/products.csv",      parse_dates=["launch_date"])
    cust = pd.read_csv("data/raw/customers.csv",     parse_dates=["signup_date"])
    stor = pd.read_csv("data/raw/stores.csv",        parse_dates=["opened_date"])
    print(f"  Transactions : {len(txn):>8,} rows")
    print(f"  Customers    : {len(cust):>8,} rows")
    print(f"  Products     : {len(prod):>8,} rows")
    print(f"  Stores       : {len(stor):>8,} rows")
    return txn, prod, cust, stor


# ── 1. Revenue distribution ───────────────────────────────────────────────────
def plot_revenue_distribution(txn):
    fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)

    data = txn.loc[txn["is_returned"] == 0, "revenue"]

    axes[0].hist(data, bins=60, color="#2471A3", edgecolor="white", linewidth=0.4)
    axes[0].set_title("Revenue per Transaction (Distribution)")
    axes[0].set_xlabel("Revenue (€)")
    axes[0].set_ylabel("Frequency")
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))

    axes[1].boxplot(data, vert=True, patch_artist=True,
                    boxprops=dict(facecolor="#AED6F1", color="#1A5276"),
                    medianprops=dict(color="#1A5276", linewidth=2))
    axes[1].set_title("Revenue per Transaction (Box Plot)")
    axes[1].set_ylabel("Revenue (€)")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    axes[1].set_xticks([])

    plt.suptitle("RetailIQ — Transaction Revenue Overview", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/01_revenue_distribution.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("  ✓ 01_revenue_distribution.png")


# ── 2. Monthly revenue trend ──────────────────────────────────────────────────
def plot_monthly_trend(txn):
    monthly = (
        txn.loc[txn["is_returned"] == 0]
           .groupby(txn["transaction_date"].dt.to_period("M"))["revenue"]
           .sum()
           .reset_index()
    )
    monthly["transaction_date"] = monthly["transaction_date"].dt.to_timestamp()

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.fill_between(monthly["transaction_date"], monthly["revenue"],
                    alpha=0.25, color="#2E86C1")
    ax.plot(monthly["transaction_date"], monthly["revenue"],
            color="#1A5276", linewidth=2.5, marker="o", markersize=4)
    ax.set_title("Monthly Revenue Trend (2023–2026)", fontsize=16)
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (€)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/02_monthly_revenue_trend.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("  ✓ 02_monthly_revenue_trend.png")


# ── 3. Category revenue bar chart ─────────────────────────────────────────────
def plot_category_revenue(txn, prod):
    merged = txn.loc[txn["is_returned"] == 0].merge(
        prod[["product_id", "category"]], on="product_id")
    cat_rev = (merged.groupby("category")["revenue"]
                     .sum()
                     .sort_values(ascending=True))

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(cat_rev.index, cat_rev.values, color=sns.color_palette("Blues_d", len(cat_rev)))
    ax.set_title("Revenue by Category", fontsize=16)
    ax.set_xlabel("Total Revenue (€)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x/1e6:.1f}M"))

    for bar in bars:
        w = bar.get_width()
        ax.text(w + max(cat_rev) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"€{w/1e6:.2f}M", va="center", fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/03_category_revenue.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("  ✓ 03_category_revenue.png")


# ── 4. Channel split (pie) ────────────────────────────────────────────────────
def plot_channel_split(txn):
    channel_rev = (txn.loc[txn["is_returned"] == 0]
                      .groupby("channel")["revenue"]
                      .sum()
                      .sort_values(ascending=False))

    fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)

    axes[0].pie(
        channel_rev, labels=channel_rev.index,
        autopct="%1.1f%%", startangle=90,
        colors=["#1F618D", "#2E86C1", "#85C1E9"],
        pctdistance=0.8, labeldistance=1.1,
        wedgeprops=dict(edgecolor="white", linewidth=1.5)
    )
    axes[0].set_title("Revenue Share by Channel")

    orders = txn.groupby("channel").size().sort_values(ascending=False)
    sns.barplot(x=orders.index, y=orders.values, ax=axes[1],
                palette=["#1F618D", "#2E86C1", "#85C1E9"])
    axes[1].set_title("Order Count by Channel")
    axes[1].set_xlabel("Channel")
    axes[1].set_ylabel("Orders")
    for p in axes[1].patches:
        axes[1].annotate(f"{int(p.get_height()):,}",
                         (p.get_x() + p.get_width() / 2, p.get_height()),
                         ha="center", va="bottom", fontsize=11)

    plt.suptitle("RetailIQ — Sales Channel Performance", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/04_channel_split.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("  ✓ 04_channel_split.png")


# ── 5. Loyalty tier analysis ──────────────────────────────────────────────────
def plot_loyalty_tiers(txn, cust):
    merged = txn.loc[txn["is_returned"] == 0].merge(
        cust[["customer_id", "loyalty_tier"]], on="customer_id")
    tier_order = ["Bronze", "Silver", "Gold", "Platinum"]
    tier_stats = (merged.groupby("loyalty_tier")
                        .agg(total_revenue=("revenue", "sum"),
                             avg_order_value=("revenue", "mean"),
                             orders=("transaction_id", "count"))
                        .reindex(tier_order))

    fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
    colors = ["#B7950B", "#839192", "#D4AC0D", "#85C1E9"]

    axes[0].bar(tier_stats.index, tier_stats["total_revenue"],
                color=colors, edgecolor="white")
    axes[0].set_title("Total Revenue by Loyalty Tier")
    axes[0].set_ylabel("Revenue (€)")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x/1e6:.1f}M"))

    axes[1].bar(tier_stats.index, tier_stats["avg_order_value"],
                color=colors, edgecolor="white")
    axes[1].set_title("Avg Order Value by Loyalty Tier")
    axes[1].set_ylabel("Avg Order Value (€)")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))

    plt.suptitle("RetailIQ — Customer Loyalty Tier Analysis", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/05_loyalty_tier_analysis.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("  ✓ 05_loyalty_tier_analysis.png")


# ── 6. Summary statistics CSV ─────────────────────────────────────────────────
def export_summary_stats(txn, prod, cust):
    clean = txn.loc[txn["is_returned"] == 0]
    stats = {
        "total_transactions":   len(txn),
        "total_revenue_eur":    round(clean["revenue"].sum(), 2),
        "avg_order_value_eur":  round(clean["revenue"].mean(), 2),
        "median_order_eur":     round(clean["revenue"].median(), 2),
        "return_rate_pct":      round(txn["is_returned"].mean() * 100, 2),
        "unique_customers":     txn["customer_id"].nunique(),
        "unique_products":      txn["product_id"].nunique(),
        "date_range_start":     str(txn["transaction_date"].min().date()),
        "date_range_end":       str(txn["transaction_date"].max().date()),
    }
    pd.DataFrame([stats]).T.rename(columns={0: "value"}).to_csv(
        f"{OUT_DIR}/summary_stats.csv")
    print("  ✓ summary_stats.csv")

    # Print to console
    print("\n  ── Summary Statistics ──")
    for k, v in stats.items():
        print(f"    {k:<30} {v}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\nRetailIQ — EDA")
    print("=" * 40)
    txn, prod, cust, stor = load_data()

    print("\nGenerating charts...")
    plot_revenue_distribution(txn)
    plot_monthly_trend(txn)
    plot_category_revenue(txn, prod)
    plot_channel_split(txn)
    plot_loyalty_tiers(txn, cust)
    export_summary_stats(txn, prod, cust)

    print(f"\nAll outputs saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()
