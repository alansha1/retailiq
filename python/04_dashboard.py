"""
RetailIQ — Interactive Streamlit Dashboard
==========================================
A web-based business intelligence dashboard powered by Streamlit
and Plotly. Covers: Revenue KPIs, Category breakdown, Customer
segmentation, Cohort retention, and Forecasting.

Usage:
    pip install streamlit plotly
    streamlit run python/04_dashboard.py

Then open http://localhost:8501 in your browser.
"""

import pandas as pd
import numpy as np
from datetime import datetime

try:
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("Install streamlit and plotly: pip install streamlit plotly")
    exit(1)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "RetailIQ Analytics",
    page_icon   = "🛍️",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1F2937; border-radius: 10px;
        padding: 16px 20px; margin-bottom: 8px;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #60A5FA; }
    .metric-delta { font-size: 0.9rem; color: #6EE7B7; }
    .stMetric label { font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    txn  = pd.read_csv("data/raw/transactions.csv", parse_dates=["transaction_date"])
    prod = pd.read_csv("data/raw/products.csv")
    cust = pd.read_csv("data/raw/customers.csv",   parse_dates=["signup_date"])
    stor = pd.read_csv("data/raw/stores.csv")
    txn  = txn.merge(prod[["product_id", "category", "brand", "cost_price"]], on="product_id")
    txn  = txn.merge(cust[["customer_id", "loyalty_tier", "city", "age_group"]], on="customer_id")
    txn["year"]  = txn["transaction_date"].dt.year
    txn["month"] = txn["transaction_date"].dt.to_period("M").dt.to_timestamp()
    txn["gross_profit"] = txn["revenue"] - txn["quantity"] * txn["cost_price"]
    return txn, prod, cust, stor

txn, prod, cust, stor = load_data()
clean = txn.loc[txn["is_returned"] == 0]

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.image("https://via.placeholder.com/200x60/1F2937/60A5FA?text=RetailIQ",
                 use_column_width=True)
st.sidebar.title("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=[txn["transaction_date"].min().date(),
           txn["transaction_date"].max().date()],
    min_value=txn["transaction_date"].min().date(),
    max_value=txn["transaction_date"].max().date(),
)
categories = st.sidebar.multiselect(
    "Categories", options=sorted(txn["category"].unique()),
    default=sorted(txn["category"].unique()))
channels = st.sidebar.multiselect(
    "Channels", options=sorted(txn["channel"].unique()),
    default=sorted(txn["channel"].unique()))

# Apply filters
mask = (
    (txn["transaction_date"].dt.date >= date_range[0]) &
    (txn["transaction_date"].dt.date <= date_range[1]) &
    (txn["category"].isin(categories)) &
    (txn["channel"].isin(channels)) &
    (txn["is_returned"] == 0)
)
filtered = txn.loc[mask].copy()

# ── Main layout ───────────────────────────────────────────────────────────────
st.title("🛍️ RetailIQ Analytics Dashboard")
st.caption(f"Data: {filtered['transaction_date'].min().date()} → "
           f"{filtered['transaction_date'].max().date()}  |  "
           f"{len(filtered):,} transactions")

# ── KPI Row ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_rev    = filtered["revenue"].sum()
avg_order    = filtered["revenue"].mean()
uniq_cust    = filtered["customer_id"].nunique()
total_orders = len(filtered)
gross_margin = filtered["gross_profit"].sum() / filtered["revenue"].sum() * 100

col1.metric("💰 Total Revenue",     f"€{total_rev:,.0f}")
col2.metric("🛒 Orders",            f"{total_orders:,}")
col3.metric("👥 Unique Customers",  f"{uniq_cust:,}")
col4.metric("📦 Avg Order Value",   f"€{avg_order:,.2f}")
col5.metric("📈 Gross Margin",      f"{gross_margin:.1f}%")

st.divider()

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Revenue Trends", "📦 Products", "👥 Customers", "🗺️ Geography", "🔮 Forecast"
])

# ── Tab 1: Revenue Trends ─────────────────────────────────────────────────────
with tab1:
    monthly = filtered.groupby("month")["revenue"].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["revenue"],
        fill="tozeroy", fillcolor="rgba(96,165,250,0.15)",
        line=dict(color="#60A5FA", width=2.5),
        mode="lines+markers", marker=dict(size=5),
        name="Monthly Revenue"
    ))
    fig.update_layout(title="Monthly Revenue Trend",
                      xaxis_title="Month", yaxis_title="Revenue (€)",
                      yaxis_tickformat="€,.0f", height=380,
                      template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        channel_rev = filtered.groupby("channel")["revenue"].sum().reset_index()
        fig_ch = px.pie(channel_rev, values="revenue", names="channel",
                        title="Revenue by Channel", hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Blues_r,
                        template="plotly_dark")
        st.plotly_chart(fig_ch, use_container_width=True)

    with col_b:
        payment_rev = filtered.groupby("payment_method")["revenue"].sum().sort_values().reset_index()
        fig_pm = px.bar(payment_rev, x="revenue", y="payment_method", orientation="h",
                        title="Revenue by Payment Method",
                        color="revenue",
                        color_continuous_scale="Blues",
                        template="plotly_dark")
        fig_pm.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_pm, use_container_width=True)

# ── Tab 2: Products ───────────────────────────────────────────────────────────
with tab2:
    cat_stats = (filtered.groupby("category")
                         .agg(revenue=("revenue", "sum"),
                              orders=("transaction_id", "count"),
                              gross_profit=("gross_profit", "sum"))
                         .reset_index())
    cat_stats["margin_pct"] = cat_stats["gross_profit"] / cat_stats["revenue"] * 100

    fig_cat = px.bar(cat_stats.sort_values("revenue", ascending=True),
                     x="revenue", y="category", orientation="h",
                     color="margin_pct", color_continuous_scale="RdYlGn",
                     title="Category Revenue & Margin %",
                     labels={"revenue": "Revenue (€)", "margin_pct": "Margin %"},
                     template="plotly_dark")
    st.plotly_chart(fig_cat, use_container_width=True)

    top_products = (filtered.groupby(["product_id", "brand", "category"])["revenue"]
                            .sum()
                            .reset_index()
                            .merge(prod[["product_id", "product_name"]], on="product_id")
                            .nlargest(15, "revenue"))
    fig_top = px.bar(top_products.sort_values("revenue"),
                     x="revenue", y="product_name", orientation="h",
                     color="category",
                     title="Top 15 Products by Revenue",
                     template="plotly_dark")
    st.plotly_chart(fig_top, use_container_width=True)

# ── Tab 3: Customers ──────────────────────────────────────────────────────────
with tab3:
    tier_order = ["Bronze", "Silver", "Gold", "Platinum"]
    tier_stats = (filtered.groupby("loyalty_tier")
                          .agg(revenue=("revenue", "sum"),
                               orders=("transaction_id", "count"),
                               customers=("customer_id", "nunique"))
                          .reindex(tier_order)
                          .reset_index())

    col1, col2 = st.columns(2)
    with col1:
        fig_tier = px.bar(tier_stats, x="loyalty_tier", y="revenue",
                          color="loyalty_tier",
                          color_discrete_map={"Bronze":"#CD7F32","Silver":"#C0C0C0",
                                              "Gold":"#FFD700","Platinum":"#85C1E9"},
                          title="Revenue by Loyalty Tier", template="plotly_dark")
        st.plotly_chart(fig_tier, use_container_width=True)

    with col2:
        age_stats = (filtered.groupby("age_group")["revenue"].sum()
                             .reset_index().sort_values("age_group"))
        fig_age = px.pie(age_stats, values="revenue", names="age_group",
                         title="Revenue by Age Group", hole=0.35,
                         template="plotly_dark")
        st.plotly_chart(fig_age, use_container_width=True)

# ── Tab 4: Geography ──────────────────────────────────────────────────────────
with tab4:
    city_stats = (filtered.groupby("city")
                          .agg(revenue=("revenue", "sum"),
                               orders=("transaction_id", "count"))
                          .reset_index()
                          .sort_values("revenue", ascending=False))
    fig_city = px.bar(city_stats, x="city", y="revenue",
                      color="revenue", color_continuous_scale="Blues",
                      title="Revenue by City", template="plotly_dark")
    fig_city.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_city, use_container_width=True)

# ── Tab 5: Forecast ───────────────────────────────────────────────────────────
with tab5:
    try:
        fc = pd.read_csv("outputs/forecast/forecast_values.csv")
        hist = (filtered.groupby("month")["revenue"]
                        .sum()
                        .reset_index()
                        .rename(columns={"month": "month", "revenue": "actual_revenue"}))

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=hist["month"], y=hist["actual_revenue"],
                                    name="Historical", line=dict(color="#60A5FA", width=2)))
        for model_name, group in fc.groupby("model"):
            fig_fc.add_trace(go.Scatter(
                x=group["month"], y=group["forecast_revenue"],
                name=f"Forecast: {model_name}", mode="lines+markers",
                line=dict(width=2, dash="dash"), marker=dict(size=6)))

        fig_fc.update_layout(title="6-Month Revenue Forecast (Multiple Models)",
                             xaxis_title="Month", yaxis_title="Revenue (€)",
                             yaxis_tickformat="€,.0f", height=450,
                             template="plotly_dark")
        st.plotly_chart(fig_fc, use_container_width=True)

        comp = pd.read_csv("outputs/forecast/model_comparison.csv", index_col=0)
        st.subheader("Model Performance (hold-out test set)")
        st.dataframe(comp.style.format({"MAE": "€{:,.0f}", "RMSE": "€{:,.0f}",
                                        "MAPE%": "{:.1f}%"}))
    except FileNotFoundError:
        st.info("Run `python python/03_forecasting.py` first to generate forecasts.")

st.sidebar.markdown("---")
st.sidebar.markdown("**RetailIQ** · Built with Python, Pandas, Plotly & Streamlit")
