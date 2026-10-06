-- ============================================================
-- RetailIQ — PostgreSQL Schema
-- ============================================================
-- Compatible with: PostgreSQL 14+, Snowflake, BigQuery (with
-- minor dialect adjustments noted in comments).
-- ============================================================

-- Drop existing tables (safe re-run)
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS products     CASCADE;
DROP TABLE IF EXISTS customers    CASCADE;
DROP TABLE IF EXISTS stores       CASCADE;
DROP TABLE IF EXISTS date_dim     CASCADE;

-- ── Dimension: Date ───────────────────────────────────────────────────────────
CREATE TABLE date_dim (
    date_key        DATE        PRIMARY KEY,
    year            SMALLINT    NOT NULL,
    quarter         SMALLINT    NOT NULL,
    month           SMALLINT    NOT NULL,
    month_name      VARCHAR(12) NOT NULL,
    week_of_year    SMALLINT    NOT NULL,
    day_of_week     SMALLINT    NOT NULL,
    day_name        VARCHAR(12) NOT NULL,
    is_weekend      BOOLEAN     NOT NULL,
    is_public_holiday BOOLEAN   DEFAULT FALSE
);

-- Populate date dimension (2020-01-01 to 2026-12-31)
-- PostgreSQL: generate_series
-- Snowflake:  use GENERATOR(ROWCOUNT => ...) equivalent
INSERT INTO date_dim (date_key, year, quarter, month, month_name,
                      week_of_year, day_of_week, day_name, is_weekend)
SELECT
    d::DATE                                             AS date_key,
    EXTRACT(YEAR    FROM d)::SMALLINT                   AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT                   AS quarter,
    EXTRACT(MONTH   FROM d)::SMALLINT                   AS month,
    TO_CHAR(d, 'Month')                                 AS month_name,
    EXTRACT(WEEK    FROM d)::SMALLINT                   AS week_of_year,
    EXTRACT(ISODOW  FROM d)::SMALLINT                   AS day_of_week,
    TO_CHAR(d, 'Day')                                   AS day_name,
    EXTRACT(ISODOW  FROM d) IN (6, 7)                  AS is_weekend
FROM generate_series('2020-01-01'::DATE, '2026-12-31'::DATE, '1 day') AS d;

-- ── Dimension: Customers ──────────────────────────────────────────────────────
CREATE TABLE customers (
    customer_id     SERIAL      PRIMARY KEY,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    city            VARCHAR(80),
    province        VARCHAR(80),
    country         VARCHAR(60) DEFAULT 'Ireland',
    signup_date     DATE,
    loyalty_tier    VARCHAR(20) CHECK (loyalty_tier IN ('Bronze','Silver','Gold','Platinum')),
    age_group       VARCHAR(10),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Dimension: Products ───────────────────────────────────────────────────────
CREATE TABLE products (
    product_id      SERIAL      PRIMARY KEY,
    product_name    VARCHAR(200) NOT NULL,
    category        VARCHAR(80)  NOT NULL,
    brand           VARCHAR(80),
    cost_price      NUMERIC(10,2) NOT NULL CHECK (cost_price >= 0),
    sale_price      NUMERIC(10,2) NOT NULL CHECK (sale_price >= 0),
    stock_level     INT          DEFAULT 0,
    is_active       BOOLEAN      DEFAULT TRUE,
    launch_date     DATE,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Dimension: Stores ─────────────────────────────────────────────────────────
CREATE TABLE stores (
    store_id        SERIAL      PRIMARY KEY,
    store_name      VARCHAR(150) NOT NULL,
    city            VARCHAR(80),
    province        VARCHAR(80),
    country         VARCHAR(60)  DEFAULT 'Ireland',
    store_type      VARCHAR(30)  CHECK (store_type IN ('Flagship','Standard','Express')),
    opened_date     DATE,
    sq_footage      INT,
    staff_count     INT,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Fact: Transactions ────────────────────────────────────────────────────────
CREATE TABLE transactions (
    transaction_id  BIGSERIAL   PRIMARY KEY,
    customer_id     INT         REFERENCES customers(customer_id),
    product_id      INT         REFERENCES products(product_id),
    store_id        INT         REFERENCES stores(store_id),  -- NULL for online
    transaction_date DATE       NOT NULL,
    channel         VARCHAR(20)  NOT NULL CHECK (channel IN ('Online','In-Store','Mobile App')),
    quantity        SMALLINT    NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10,2) NOT NULL,
    discount_pct    NUMERIC(5,2)  DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 1),
    revenue         NUMERIC(12,2) NOT NULL,
    payment_method  VARCHAR(30),
    is_returned     BOOLEAN      DEFAULT FALSE,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX idx_txn_date        ON transactions (transaction_date);
CREATE INDEX idx_txn_customer    ON transactions (customer_id);
CREATE INDEX idx_txn_product     ON transactions (product_id);
CREATE INDEX idx_txn_channel     ON transactions (channel);
CREATE INDEX idx_products_cat    ON products (category);
CREATE INDEX idx_customers_tier  ON customers (loyalty_tier);
CREATE INDEX idx_customers_city  ON customers (city);

-- ── Load CSV data (psql \copy) ────────────────────────────────────────────────
-- Run from project root:
--   psql -U postgres -d retailiq -f sql/01_schema_postgresql.sql
--   \copy customers    FROM 'data/raw/customers.csv'    CSV HEADER;
--   \copy products     FROM 'data/raw/products.csv'     CSV HEADER;
--   \copy stores       FROM 'data/raw/stores.csv'       CSV HEADER;
--   \copy transactions FROM 'data/raw/transactions.csv' CSV HEADER;
