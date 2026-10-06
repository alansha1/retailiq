# RetailIQ — End-to-End Retail Analytics Platform

> A portfolio project demonstrating the full modern data analytics stack:  
> **Python · SQL · Pandas · Scikit-learn · Streamlit · Power BI · Tableau · PostgreSQL · Snowflake**

---

## Overview

RetailIQ is a production-style data analytics project built around a synthetic Irish retail dataset (50,000 transactions, 5,000 customers, 500 products, 10 stores). It demonstrates the complete analytics workflow — from raw data generation through SQL modelling, Python analysis, machine learning, and interactive dashboards.

**Why this project?** Most portfolio projects show one tool. This project shows how all the tools fit together as a real data team would use them.

---

## Project Structure

```
RetailIQ/
├── data/
│   ├── generate_data.py        # Synthetic dataset generator
│   └── raw/                    # Generated CSVs (git-ignored)
│
├── sql/
│   ├── 01_schema_postgresql.sql    # Star-schema DDL (PostgreSQL-compatible)
│   ├── 02_analysis_queries.sql     # Core analytics SQL (10 query categories)
│   └── 03_snowflake_notes.sql      # Snowflake-specific adaptations
│
├── python/
│   ├── 01_eda.py               # Exploratory data analysis & charts
│   ├── 02_rfm_segmentation.py  # RFM customer segmentation model
│   ├── 03_forecasting.py       # Revenue forecasting (Linear, ARIMA)
│   └── 04_dashboard.py         # Interactive Streamlit dashboard
│
├── dashboards/
│   └── README.md               # Power BI, Tableau, Looker Studio setup
│
├── outputs/                    # Generated charts & CSVs (git-ignored)
├── requirements.txt
└── .gitignore
```

---

## Quick Start

### 1. Clone & install dependencies
```bash
git clone https://github.com/alansha1/retailiq.git
cd RetailIQ
pip install -r requirements.txt
```

### 2. Generate the dataset
```bash
python data/generate_data.py
# Options: --customers 5000 --transactions 50000 --seed 42
```

### 3. Load into PostgreSQL (optional)
```bash
createdb retailiq
psql -d retailiq -f sql/01_schema_postgresql.sql
# Then run the \copy commands shown at the bottom of the file
```

### 4. Run the analysis scripts
```bash
python python/01_eda.py            # EDA charts → outputs/eda/
python python/02_rfm_segmentation.py   # RFM model → outputs/rfm/
python python/03_forecasting.py    # Forecast   → outputs/forecast/
```

### 5. Launch the Streamlit dashboard
```bash
streamlit run python/04_dashboard.py
# Opens at http://localhost:8501
```

---

## What Each Component Demonstrates

### Data Engineering
- **Synthetic data generation** — realistic retail distributions, seasonal patterns
- **Star schema design** — fact/dimension tables with proper foreign keys and indexes
- **ETL pattern** — CSV → PostgreSQL → aggregated views

### SQL Analytics
| Query | Technique |
|-------|-----------|
| Monthly revenue trend | `DATE_TRUNC`, window functions |
| Category margin analysis | `JOIN`, aggregation, computed margins |
| RFM scoring | `NTILE()`, `CASE WHEN`, CTEs |
| Cohort retention | Self-join, `EXTRACT(MONTH FROM AGE(...))` |
| YoY comparison | `LAG()` with 4-period offset |
| Store performance | Joined aggregation with KPIs per employee |

### Python & Machine Learning
| Script | Libraries | Techniques |
|--------|-----------|------------|
| `01_eda.py` | Pandas, Seaborn, Matplotlib | Distributions, trend analysis, correlation |
| `02_rfm_segmentation.py` | Pandas, NumPy | Quintile scoring, customer segmentation |
| `03_forecasting.py` | Scikit-learn, Statsmodels | Linear regression, ARIMA, MAE/RMSE/MAPE |
| `04_dashboard.py` | Streamlit, Plotly | Interactive BI dashboard |

### Business Intelligence
- **Power BI** — Star schema model, DAX measures, report pages (see `dashboards/README.md`)
- **Tableau** — Blended data source, calculated fields, worksheets
- **Snowflake** — Time Travel, Dynamic Tables, Streams & Tasks, VARIANT columns
- **Streamlit** — Web-based self-service analytics with filters

---

## Sample Analyses

### Revenue Trend
Monthly revenue from 2023–2026 broken down by channel, with seasonal patterns and MoM growth rates.

### RFM Customer Segments
Customers classified into 7 segments — from **Champions** (high R, F, M scores) to **Lost / Inactive** — enabling targeted re-engagement campaigns.

| Segment | Typical Action |
|---------|---------------|
| Champions | Reward, upsell premium |
| Loyal Customers | Loyalty programme perks |
| At Risk | Win-back email, discount |
| Lost / Inactive | Survey, last-chance offer |
| New Customers | Onboarding sequence |

### Forecasting Models
Three models compared on a held-out test set:
- **Linear Trend** — baseline model, interpretable
- **Polynomial Regression** — captures non-linear growth
- **ARIMA(2,1,1)** — accounts for autocorrelation and seasonality

Performance evaluated using MAE, RMSE, and MAPE. Outputs a 6-month forward forecast with confidence intervals.

---

## Tools & Technologies Used

| Category | Tools |
|----------|-------|
| **Languages** | Python 3.10+, SQL |
| **Data manipulation** | Pandas, NumPy |
| **Visualisation** | Matplotlib, Seaborn, Plotly |
| **Machine Learning** | Scikit-learn, Statsmodels (ARIMA) |
| **BI Dashboard** | Streamlit |
| **Databases** | PostgreSQL, Snowflake (notes) |
| **BI Tools** | Power BI, Tableau, Looker Studio |
| **Version Control** | Git & GitHub |

---

## Skills Demonstrated

- Designing and querying a relational star schema
- Writing production-grade SQL (CTEs, window functions, cohort analysis)
- Exploratory data analysis and statistical summarisation
- Customer segmentation using RFM methodology
- Time-series forecasting and model evaluation
- Building interactive data applications with Streamlit and Plotly
- Translating analytical findings into business recommendations
- Cross-tool fluency: same data, multiple platforms

---

## Author

**Alan Sha** — MSc Data Analytics (Dublin Business School, 2026)  
[github.com/alansha1](https://github.com/alansha1) · [linkedin.com/in/alan-sha](https://linkedin.com/in/alan-sha)
