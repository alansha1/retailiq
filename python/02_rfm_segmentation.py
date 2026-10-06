"""
RetailIQ — RFM Customer Segmentation
=====================================
Builds an RFM (Recency, Frequency, Monetary) model to segment
customers into actionable groups for targeted marketing.

Output:  outputs/rfm/  (charts + rfm_scores.csv)

Usage:
    python python/02_rfm_segmentation.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from datetime import datetime

OUT_DIR = "outputs/rfm"
os.makedirs(OUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")

SEGMENT_COLORS = {
    "Champions":          "#1A5276",
    "Loyal Customers":    "#2E86C1",
    "Potential Loyalists":"#5DADE2",
    "New Customers":      "#85C1E9",
    "Needs Attention":    "#F39C12",
    "At Risk":            "#E67E22",
    "Lost / Inactive":    "#C0392B",
}


# ── Build RFM table ───────────────────────────────────────────────────────────
def build_rfm(txn: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    """Compute R, F, M metrics for each customer."""
    clean = txn.loc[txn["is_returned"] == 0].copy()

    rfm = (clean.groupby("customer_id")
                .agg(
                    last_purchase  = ("transaction_date", "max"),
                    frequency      = ("transaction_id",   "count"),
                    monetary       = ("revenue",          "sum"),
                )
                .reset_index())

    rfm["recency_days"] = (snapshot_date - rfm["last_purchase"]).dt.days
    return rfm


# ── Score customers 1-5 ───────────────────────────────────────────────────────
def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    rfm = rfm.copy()

    # Recency: lower days = higher score (more recent = better)
    rfm["r_score"] = pd.qcut(rfm["recency_days"], q=5,
                              labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5,
                              labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), q=5,
                              labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    return rfm


# ── Assign segments ───────────────────────────────────────────────────────────
def assign_segment(row) -> str:
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "New Customers"
    elif r >= 3 and m >= 4:
        return "Potential Loyalists"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 1:
        return "Lost / Inactive"
    else:
        return "Needs Attention"


# ── Charts ────────────────────────────────────────────────────────────────────
def plot_segment_distribution(rfm: pd.DataFrame):
    seg_counts = rfm["segment"].value_counts()
    colors = [SEGMENT_COLORS.get(s, "#999") for s in seg_counts.index]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Pie
    wedges, texts, autotexts = axes[0].pie(
        seg_counts, labels=None, autopct="%1.1f%%",
        startangle=90, colors=colors,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
        pctdistance=0.82)
    for t in autotexts:
        t.set_fontsize(10)
    axes[0].legend(wedges, seg_counts.index, loc="lower left",
                   bbox_to_anchor=(-0.05, -0.1), fontsize=10)
    axes[0].set_title("Customer Distribution by Segment")

    # Bar
    axes[1].barh(seg_counts.index[::-1], seg_counts.values[::-1], color=colors[::-1])
    axes[1].set_title("Customer Count by RFM Segment")
    axes[1].set_xlabel("Customers")
    for i, (idx, val) in enumerate(zip(seg_counts.index[::-1], seg_counts.values[::-1])):
        axes[1].text(val + 10, i, f"{val:,}", va="center")

    plt.suptitle("RetailIQ — RFM Customer Segmentation", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/01_segment_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ 01_segment_distribution.png")


def plot_segment_value(rfm: pd.DataFrame):
    seg_value = (rfm.groupby("segment")
                    .agg(avg_monetary=("monetary", "mean"),
                         avg_frequency=("frequency", "mean"),
                         avg_recency=("recency_days", "mean"),
                         customers=("customer_id", "count"))
                    .sort_values("avg_monetary", ascending=False))

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    colors = [SEGMENT_COLORS.get(s, "#999") for s in seg_value.index]

    for ax, col, label, fmt in zip(
        axes,
        ["avg_monetary", "avg_frequency", "avg_recency"],
        ["Avg Spend (€)", "Avg Orders", "Avg Recency (days)"],
        ["€{:,.0f}", "{:.1f}", "{:.0f} days"]
    ):
        bars = ax.barh(seg_value.index[::-1], seg_value[col][::-1], color=colors[::-1])
        ax.set_title(label)
        ax.set_xlabel(label)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + max(seg_value[col]) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    fmt.format(w), va="center", fontsize=9)

    plt.suptitle("RetailIQ — RFM Segment Value Metrics", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/02_segment_value_metrics.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ 02_segment_value_metrics.png")


def plot_rfm_heatmap(rfm: pd.DataFrame):
    """R vs F frequency heatmap — classic RFM grid."""
    pivot = (rfm.groupby(["r_score", "f_score"])["customer_id"]
                .count()
                .unstack(fill_value=0))

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd",
                linewidths=0.5, ax=ax)
    ax.set_title("RFM Grid: Recency vs Frequency\n(cell = number of customers)", fontsize=14)
    ax.set_xlabel("Frequency Score (1=Low, 5=High)")
    ax.set_ylabel("Recency Score (1=Low, 5=High)")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/03_rfm_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ 03_rfm_heatmap.png")


def plot_monetary_by_segment(rfm: pd.DataFrame):
    """Box plot of spend distribution per segment."""
    order = list(SEGMENT_COLORS.keys())
    order = [s for s in order if s in rfm["segment"].unique()]

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.boxplot(data=rfm, x="segment", y="monetary", order=order,
                palette=[SEGMENT_COLORS[s] for s in order], ax=ax)
    ax.set_title("Spend Distribution per RFM Segment", fontsize=16)
    ax.set_xlabel("")
    ax.set_ylabel("Total Spend (€)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/04_monetary_boxplot.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ 04_monetary_boxplot.png")


# ── Export ────────────────────────────────────────────────────────────────────
def export_rfm_csv(rfm: pd.DataFrame):
    out_cols = ["customer_id", "recency_days", "frequency", "monetary",
                "r_score", "f_score", "m_score", "rfm_score", "segment"]
    rfm[out_cols].sort_values("rfm_score", ascending=False).to_csv(
        f"{OUT_DIR}/rfm_scores.csv", index=False)
    print("  ✓ rfm_scores.csv")

    # Segment summary
    summary = (rfm.groupby("segment")
                  .agg(customers=("customer_id", "count"),
                       avg_spend=("monetary", "mean"),
                       total_spend=("monetary", "sum"),
                       avg_orders=("frequency", "mean"))
                  .round(2)
                  .sort_values("total_spend", ascending=False))
    summary.to_csv(f"{OUT_DIR}/segment_summary.csv")
    print("  ✓ segment_summary.csv")
    print("\n  ── Segment Summary ──")
    print(summary.to_string())


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\nRetailIQ — RFM Segmentation")
    print("=" * 40)

    txn = pd.read_csv("data/raw/transactions.csv", parse_dates=["transaction_date"])
    snapshot = txn["transaction_date"].max() + pd.Timedelta(days=1)
    print(f"  Snapshot date: {snapshot.date()}")

    rfm = build_rfm(txn, snapshot)
    rfm = score_rfm(rfm)
    rfm["segment"] = rfm.apply(assign_segment, axis=1)

    print(f"\n  {rfm['segment'].nunique()} segments identified across {len(rfm):,} customers")

    print("\nGenerating charts...")
    plot_segment_distribution(rfm)
    plot_segment_value(rfm)
    plot_rfm_heatmap(rfm)
    plot_monetary_by_segment(rfm)
    export_rfm_csv(rfm)

    print(f"\nAll outputs saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()
