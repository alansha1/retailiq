# RetailIQ — Dashboard & BI Tool Setup Guide

This folder contains setup notes and connection guides for building
dashboards in **Power BI**, **Tableau**, and **Looker Studio** using
the RetailIQ dataset.

---

## Power BI

### Connection Options
| Source | Steps |
|--------|-------|
| **CSV files** | Get Data → Text/CSV → `data/raw/*.csv` |
| **PostgreSQL** | Get Data → Database → PostgreSQL → `localhost/retailiq` |
| **Snowflake** | Get Data → Database → Snowflake → enter account identifier |

### Recommended Data Model (Star Schema)
```
         ┌──────────────┐
         │  date_dim    │
         └──────┬───────┘
                │
┌─────────┐  ┌─┴──────────────┐  ┌─────────┐
│customers│──┤  transactions  ├──│products │
└─────────┘  └───────┬────────┘  └─────────┘
                      │
                ┌─────┴──────┐
                │   stores   │
                └────────────┘
```

### Key DAX Measures

```dax
-- Total Revenue
Total Revenue = 
    CALCULATE(
        SUM(transactions[revenue]),
        transactions[is_returned] = 0
    )

-- Revenue MoM %
Revenue MoM % = 
    VAR current  = [Total Revenue]
    VAR previous = CALCULATE([Total Revenue], DATEADD('date_dim'[date_key], -1, MONTH))
    RETURN DIVIDE(current - previous, previous) * 100

-- Average Order Value
Avg Order Value = 
    DIVIDE([Total Revenue], COUNTROWS(transactions))

-- Gross Margin %
Gross Margin % = 
    DIVIDE(
        SUM(transactions[revenue]) - SUMX(transactions, transactions[quantity] * RELATED(products[cost_price])),
        SUM(transactions[revenue])
    ) * 100

-- Customer LTV (lifetime value)
Customer LTV = 
    DIVIDE([Total Revenue], DISTINCTCOUNT(transactions[customer_id]))

-- Return Rate
Return Rate % = 
    DIVIDE(
        COUNTROWS(FILTER(transactions, transactions[is_returned] = 1)),
        COUNTROWS(transactions)
    ) * 100
```

### Suggested Report Pages

1. **Executive Summary** — Revenue KPIs, trend line, MoM comparison
2. **Product Performance** — Category breakdown, top products, margin analysis
3. **Customer Insights** — Loyalty tier analysis, age group revenue, LTV
4. **Channel Analysis** — Online vs In-Store vs Mobile revenue split
5. **Store Performance** — Map visual, revenue per store, staff efficiency
6. **Forecast** — Import `outputs/forecast/forecast_values.csv` for overlay

---

## Tableau

### Connection Steps
1. Open Tableau Desktop
2. Connect → Text File → `data/raw/transactions.csv`
3. Add additional files via New Union or Relationships:
   - `products.csv` → join on `product_id`
   - `customers.csv` → join on `customer_id`
   - `stores.csv` → join on `store_id`

### Key Calculated Fields

```
// Revenue (excluding returns)
IF [Is Returned] = 0 THEN [Revenue] END

// Gross Profit
[Revenue] - ([Quantity] * [Cost Price])

// Gross Margin %
([Revenue] - ([Quantity] * [Cost Price])) / [Revenue]

// Days Since Last Purchase (for RFM)
DATEDIFF('day', [Transaction Date], TODAY())
```

### Suggested Worksheets

| Sheet | Chart Type | Key Dimensions |
|-------|------------|----------------|
| Monthly Revenue | Line | Month, Revenue |
| Category Mix | Bar | Category, Revenue |
| Channel Split | Donut | Channel |
| Loyalty Tiers | Bar | Tier, Revenue, Customers |
| City Map | Map | City, Revenue (size) |
| Product Margin | Scatter | Revenue vs Margin% |

---

## Looker Studio (Google Data Studio)

### Connection
- Connect to BigQuery (if using GCP) or upload CSVs via Google Sheets
- Use Google Sheets as a simple connector for the raw CSVs

### Report Setup
1. Create blended data source joining `transactions` + `products` + `customers`
2. Add calculated fields for Gross Profit and Margin %
3. Build scorecards for top KPIs
4. Add date-range control linked to `transaction_date`

---

## Tips for All Tools

- **Always filter out returns** (`is_returned = 0 / FALSE`) before KPI calculations
- **Use the date dimension** for proper calendar groupings (quarter, week)
- **Segment by loyalty_tier** to show premium customer value
- **Compare channels** — typically Online has higher AOV, In-Store has higher volume
- **Margin analysis** requires joining to `products.cost_price`
