-- ============================================================
-- RetailIQ — Core Analytics Queries
-- ============================================================
-- Covers: Revenue trends, customer segmentation, product
-- performance, cohort analysis, and RFM scoring.
-- Compatible with PostgreSQL, Snowflake, BigQuery (minor
-- dialect notes inline where needed).
-- ============================================================


-- ── 1. Monthly Revenue & Order Volume ────────────────────────────────────────
-- KPI: How is top-line revenue trending month over month?

WITH monthly AS (
    SELECT
        DATE_TRUNC('month', transaction_date)   AS month,
        SUM(revenue)                            AS total_revenue,
        COUNT(DISTINCT transaction_id)          AS total_orders,
        COUNT(DISTINCT customer_id)             AS unique_customers,
        SUM(quantity)                           AS units_sold,
        AVG(revenue)                            AS avg_order_value
    FROM transactions
    WHERE is_returned = FALSE
    GROUP BY 1
)
SELECT
    month,
    ROUND(total_revenue::NUMERIC, 2)                                                    AS total_revenue,
    total_orders,
    unique_customers,
    units_sold,
    ROUND(avg_order_value::NUMERIC, 2)                                                  AS avg_order_value,
    ROUND(
        100.0 * (total_revenue - LAG(total_revenue) OVER (ORDER BY month))
              / NULLIF(LAG(total_revenue) OVER (ORDER BY month), 0), 2
    )                                                                                   AS revenue_mom_pct
FROM monthly
ORDER BY month;


-- ── 2. Category Revenue Breakdown ────────────────────────────────────────────
-- KPI: Which categories drive the most revenue and margin?

SELECT
    p.category,
    COUNT(DISTINCT t.transaction_id)                        AS orders,
    SUM(t.quantity)                                         AS units_sold,
    ROUND(SUM(t.revenue)::NUMERIC, 2)                       AS total_revenue,
    ROUND(SUM(t.quantity * p.cost_price)::NUMERIC, 2)       AS total_cost,
    ROUND((SUM(t.revenue) - SUM(t.quantity * p.cost_price))::NUMERIC, 2)  AS gross_profit,
    ROUND(
        100.0 * (SUM(t.revenue) - SUM(t.quantity * p.cost_price))
              / NULLIF(SUM(t.revenue), 0), 2
    )                                                        AS margin_pct,
    ROUND(SUM(t.revenue) / COUNT(DISTINCT t.transaction_id)::NUMERIC, 2) AS avg_order_value
FROM transactions t
JOIN products p USING (product_id)
WHERE t.is_returned = FALSE
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ── 3. Top 20 Products by Revenue ────────────────────────────────────────────

SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    SUM(t.quantity)                                         AS units_sold,
    ROUND(SUM(t.revenue)::NUMERIC, 2)                       AS total_revenue,
    ROUND(AVG(t.unit_price)::NUMERIC, 2)                    AS avg_selling_price,
    ROUND(AVG(t.discount_pct) * 100, 2)                     AS avg_discount_pct,
    ROUND(
        (SUM(t.revenue) - SUM(t.quantity * p.cost_price))::NUMERIC, 2
    )                                                        AS gross_profit
FROM transactions t
JOIN products p USING (product_id)
WHERE t.is_returned = FALSE
GROUP BY p.product_id, p.product_name, p.category, p.brand
ORDER BY total_revenue DESC
LIMIT 20;


-- ── 4. Channel Performance ────────────────────────────────────────────────────
-- KPI: Online vs In-Store vs Mobile App split

SELECT
    channel,
    COUNT(DISTINCT customer_id)                             AS unique_customers,
    COUNT(DISTINCT transaction_id)                          AS orders,
    ROUND(SUM(revenue)::NUMERIC, 2)                         AS total_revenue,
    ROUND(AVG(revenue)::NUMERIC, 2)                         AS avg_order_value,
    ROUND(AVG(discount_pct) * 100, 2)                       AS avg_discount_pct,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS order_share_pct
FROM transactions
WHERE is_returned = FALSE
GROUP BY channel
ORDER BY total_revenue DESC;


-- ── 5. Customer Loyalty Tier Analysis ────────────────────────────────────────

SELECT
    c.loyalty_tier,
    COUNT(DISTINCT c.customer_id)                           AS customers,
    COUNT(DISTINCT t.transaction_id)                        AS total_orders,
    ROUND(SUM(t.revenue)::NUMERIC, 2)                       AS total_revenue,
    ROUND(AVG(t.revenue)::NUMERIC, 2)                       AS avg_order_value,
    ROUND(SUM(t.revenue) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
FROM customers c
LEFT JOIN transactions t USING (customer_id)
WHERE t.is_returned = FALSE OR t.is_returned IS NULL
GROUP BY c.loyalty_tier
ORDER BY CASE c.loyalty_tier
    WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2
    WHEN 'Silver'   THEN 3 WHEN 'Bronze' THEN 4 END;


-- ── 6. RFM Scoring (Recency, Frequency, Monetary) ────────────────────────────
-- Used for customer segmentation and targeted marketing

WITH rfm_base AS (
    SELECT
        customer_id,
        MAX(transaction_date)                   AS last_purchase,
        COUNT(DISTINCT transaction_id)          AS frequency,
        ROUND(SUM(revenue)::NUMERIC, 2)         AS monetary
    FROM transactions
    WHERE is_returned = FALSE
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        last_purchase,
        frequency,
        monetary,
        -- Recency: higher score = more recent
        NTILE(5) OVER (ORDER BY last_purchase DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)       AS m_score
    FROM rfm_base
),
rfm_segments AS (
    SELECT
        customer_id,
        r_score,
        f_score,
        m_score,
        (r_score + f_score + m_score)           AS rfm_total,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3                   THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score <= 2                   THEN 'New Customers'
            WHEN r_score >= 3 AND m_score >= 4                   THEN 'Potential Loyalists'
            WHEN r_score <= 2 AND f_score >= 3                   THEN 'At Risk'
            WHEN r_score <= 1                                     THEN 'Lost / Inactive'
            ELSE 'Needs Attention'
        END                                     AS segment
    FROM rfm_scores
)
SELECT
    segment,
    COUNT(*)                                    AS customers,
    ROUND(AVG(rfm_total), 2)                    AS avg_rfm_score,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM rfm_segments
GROUP BY segment
ORDER BY avg_rfm_score DESC;


-- ── 7. Cohort Retention Analysis ─────────────────────────────────────────────
-- Month-0 cohort: first purchase month; track repeat purchases per cohort

WITH first_purchase AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(transaction_date))  AS cohort_month
    FROM transactions
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        fp.customer_id,
        fp.cohort_month,
        DATE_TRUNC('month', t.transaction_date)     AS activity_month,
        -- months since first purchase
        EXTRACT(YEAR  FROM AGE(DATE_TRUNC('month', t.transaction_date), fp.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', t.transaction_date), fp.cohort_month)) AS months_since_first
    FROM first_purchase fp
    JOIN transactions t USING (customer_id)
)
SELECT
    cohort_month,
    months_since_first,
    COUNT(DISTINCT customer_id)                     AS active_customers
FROM cohort_activity
WHERE months_since_first <= 11
GROUP BY cohort_month, months_since_first
ORDER BY cohort_month, months_since_first;


-- ── 8. Store Performance (In-Store channel only) ──────────────────────────────

SELECT
    s.store_id,
    s.store_name,
    s.city,
    s.store_type,
    COUNT(DISTINCT t.transaction_id)            AS orders,
    COUNT(DISTINCT t.customer_id)               AS unique_customers,
    ROUND(SUM(t.revenue)::NUMERIC, 2)           AS total_revenue,
    ROUND(AVG(t.revenue)::NUMERIC, 2)           AS avg_order_value,
    ROUND(SUM(t.revenue) / s.staff_count, 2)    AS revenue_per_staff
FROM stores s
JOIN transactions t USING (store_id)
WHERE t.is_returned = FALSE
GROUP BY s.store_id, s.store_name, s.city, s.store_type, s.staff_count
ORDER BY total_revenue DESC;


-- ── 9. Year-over-Year Revenue Comparison ─────────────────────────────────────

SELECT
    EXTRACT(YEAR FROM transaction_date)         AS year,
    EXTRACT(QUARTER FROM transaction_date)      AS quarter,
    ROUND(SUM(revenue)::NUMERIC, 2)             AS total_revenue,
    COUNT(DISTINCT transaction_id)              AS orders,
    COUNT(DISTINCT customer_id)                 AS customers,
    ROUND(
        100.0 * (SUM(revenue) - LAG(SUM(revenue), 4) OVER (ORDER BY EXTRACT(YEAR FROM transaction_date), EXTRACT(QUARTER FROM transaction_date)))
              / NULLIF(LAG(SUM(revenue), 4) OVER (ORDER BY EXTRACT(YEAR FROM transaction_date), EXTRACT(QUARTER FROM transaction_date)), 0), 2
    )                                           AS revenue_yoy_pct
FROM transactions
WHERE is_returned = FALSE
GROUP BY 1, 2
ORDER BY 1, 2;


-- ── 10. Product Return Rate by Category ──────────────────────────────────────

SELECT
    p.category,
    COUNT(*)                                            AS total_transactions,
    SUM(CASE WHEN t.is_returned THEN 1 ELSE 0 END)     AS returns,
    ROUND(
        100.0 * SUM(CASE WHEN t.is_returned THEN 1 ELSE 0 END) / COUNT(*), 2
    )                                                   AS return_rate_pct,
    ROUND(SUM(CASE WHEN t.is_returned THEN t.revenue ELSE 0 END)::NUMERIC, 2) AS returned_revenue
FROM transactions t
JOIN products p USING (product_id)
GROUP BY p.category
ORDER BY return_rate_pct DESC;
