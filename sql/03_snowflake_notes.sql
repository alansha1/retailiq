-- ============================================================
-- RetailIQ — Snowflake Dialect Notes & Adaptations
-- ============================================================
-- These snippets show how the core queries (02_analysis_queries.sql)
-- adapt to Snowflake-specific syntax and features.
-- ============================================================


-- ── 1. Loading CSV from Snowflake Stage ──────────────────────────────────────
-- In Snowflake, data typically lands in an S3/GCS/Azure stage first.

-- Create a file format
CREATE OR REPLACE FILE FORMAT retailiq_csv
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('NULL', '');

-- Create a named stage (pointing to your S3 bucket)
-- CREATE OR REPLACE STAGE retailiq_stage
--     URL = 's3://your-bucket/retailiq/'
--     CREDENTIALS = (AWS_KEY_ID = '...' AWS_SECRET_KEY = '...');

-- Load table
-- COPY INTO transactions
--     FROM @retailiq_stage/transactions.csv
--     FILE_FORMAT = (FORMAT_NAME = retailiq_csv)
--     ON_ERROR = 'CONTINUE';


-- ── 2. Date Dimension — Snowflake Generator ───────────────────────────────────
-- Snowflake uses GENERATOR instead of generate_series

CREATE OR REPLACE TABLE date_dim AS
SELECT
    DATEADD('day', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2020-01-01'::DATE)   AS date_key,
    YEAR(date_key)                          AS year,
    QUARTER(date_key)                       AS quarter,
    MONTH(date_key)                         AS month,
    MONTHNAME(date_key)                     AS month_name,
    WEEKOFYEAR(date_key)                    AS week_of_year,
    DAYOFWEEK(date_key)                     AS day_of_week,
    DAYNAME(date_key)                       AS day_name,
    DAYOFWEEK(date_key) IN (0, 6)          AS is_weekend
FROM TABLE(GENERATOR(ROWCOUNT => 2557))     -- 7 years × 365.25
WHERE date_key <= '2026-12-31';


-- ── 3. Snowflake Time Travel ──────────────────────────────────────────────────
-- Query data as it existed 24 hours ago — great for debugging pipelines

SELECT COUNT(*) FROM transactions
AT (OFFSET => -86400);   -- 86400 seconds = 24 hours

-- Or by timestamp:
-- AT (TIMESTAMP => '2025-01-15 09:00:00'::TIMESTAMP_LTZ)


-- ── 4. Clustering Keys ────────────────────────────────────────────────────────
-- Snowflake auto-clusters, but explicit keys improve large table scans

ALTER TABLE transactions
    CLUSTER BY (transaction_date, channel);


-- ── 5. Dynamic Tables (Snowflake) ────────────────────────────────────────────
-- Auto-refreshing materialized views — ideal for dashboards

CREATE OR REPLACE DYNAMIC TABLE daily_revenue_summary
    TARGET_LAG = '1 hour'
    WAREHOUSE  = 'ANALYTICS_WH'
AS
SELECT
    transaction_date,
    channel,
    SUM(revenue)                AS total_revenue,
    COUNT(*)                    AS orders,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM transactions
WHERE is_returned = FALSE
GROUP BY transaction_date, channel;


-- ── 6. Snowpark Python UDF example ───────────────────────────────────────────
-- (for illustration — runs in Snowflake's Python sandbox)

/*
CREATE OR REPLACE FUNCTION classify_order_size(revenue FLOAT)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
HANDLER = 'classify'
AS $$
def classify(revenue):
    if revenue < 50:    return 'Small'
    elif revenue < 200: return 'Medium'
    elif revenue < 500: return 'Large'
    else:               return 'Enterprise'
$$;

SELECT classify_order_size(revenue) AS order_size, COUNT(*) AS orders
FROM transactions
GROUP BY 1;
*/


-- ── 7. VARIANT / Semi-Structured Data ────────────────────────────────────────
-- Snowflake handles JSON natively — useful for product metadata

ALTER TABLE products ADD COLUMN attributes VARIANT;

-- Query nested JSON:
-- SELECT attributes:colour::STRING AS colour
-- FROM products
-- WHERE attributes:colour IS NOT NULL;


-- ── 8. Streams & Tasks (Change Data Capture) ─────────────────────────────────
-- Track incremental changes to transactions table

CREATE OR REPLACE STREAM transactions_stream
    ON TABLE transactions
    APPEND_ONLY = TRUE;

-- Process new rows every hour:
-- CREATE OR REPLACE TASK process_new_transactions
--     WAREHOUSE = 'ANALYTICS_WH'
--     SCHEDULE = 'USING CRON 0 * * * * UTC'
-- AS
--     INSERT INTO transactions_summary
--     SELECT DATE_TRUNC('day', transaction_date), SUM(revenue)
--     FROM transactions_stream
--     GROUP BY 1;
