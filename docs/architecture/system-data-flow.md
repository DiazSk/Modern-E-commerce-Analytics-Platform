# System Data Flow

End-to-end data flow from source systems through transformation to the analytics layer.

---

## High-Level Architecture

### Star Schema Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANALYTICS LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      customer_lifetime_value                             │   │
│  │  • Total revenue & order metrics                         │   │
│  │  • Customer lifetime calculations                        │   │
│  │  • RFM Segmentation (Value/Recency/Frequency)           │   │
│  └──────────────────────┬──────────────────────────────────┘   │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                    MARTS LAYER (Core)                           │
│                          │                                      │
│       ┌──────────────────┴──────────────────┐                  │
│       │          fact_orders                │                  │
│       │  • order_item_key (PK)              │                  │
│       │  • customer_key (FK) ───────────────┼──┐               │
│       │  • product_key (FK) ────────────────┼──┼──┐            │
│       │  • date_key (FK) ───────────────────┼──┼──┼──┐         │
│       │  • quantity, price, discount        │  │  │  │         │
│       │  • line_total, order_total          │  │  │  │         │
│       └─────────────────────────────────────┘  │  │  │         │
│                                                 │  │  │         │
│  ┌──────────────────────┐  ┌─────────────────┐│  │  │         │
│  │   dim_customers      │  │  dim_products   ││  │  │         │
│  │  (SCD Type 2)        │  │                 ││  │  │         │
│  ├──────────────────────┤  ├─────────────────┤│  │  │         │
│  │ customer_key (PK) ◄──┼──┘  │ product_key ◄─┼──┘  │         │
│  │ customer_id          │     │   (PK)        │     │         │
│  │ email                │     │ product_id    │     │         │
│  │ full_name            │     │ product_name  │     │         │
│  │ customer_segment     │     │ category      │     │         │
│  │ effective_date       │     │ price         │     │         │
│  │ expiration_date      │     │ price_tier    │     │         │
│  │ is_current           │     │ rating        │     │         │
│  └──────────────────────┘     └───────────────┘     │         │
│                                                      │         │
│                          ┌───────────────────────────┘         │
│                          │      dim_date                       │
│                          ├──────────────────────┐              │
│                          │ date_key (PK) ◄──────┘              │
│                          │ date_day (NK)                       │
│                          │ year, quarter, month                │
│                          │ week_of_year                        │
│                          │ is_weekend, is_weekday              │
│                          │ month_name, day_name                │
│                          └─────────────────────────            │
└─────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼──────────────────────────────┐
│                          STAGING LAYER                          │
│                                   │                             │
│  ┌──────────────┐  ┌─────────────┴────┐  ┌──────────────┐     │
│  │stg_customers │  │   stg_orders     │  │stg_products  │     │
│  │              │  │                  │  │              │     │
│  │stg_order_items│ │   stg_events    │  │              │     │
│  └──────────────┘  └──────────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼──────────────────────────────┐
│                           SOURCE LAYER                          │
│  PostgreSQL DB                    │         S3 Data Lake        │
│  • customers                      │    • clickstream events     │
│  • orders                         │    • API products           │
│  • order_items                    │                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Incremental Loading (Daily Updates)

```
┌───────────────────────────────────────────────────────────────┐
│  STEP 1: Source Data Ingestion (Airflow)                     │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ PostgreSQL Extract → S3 Landing → PostgreSQL Staging │    │
│  │ API Fetch → S3 Landing → PostgreSQL Staging          │    │
│  │ Clickstream → S3 Partitioned → PostgreSQL Staging    │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│  STEP 2: Staging Layer (dbt)                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ stg_customers    (materialized=view)                 │    │
│  │ stg_orders       (materialized=view)                 │    │
│  │ stg_order_items  (materialized=view)                 │    │
│  │ stg_products     (materialized=view)                 │    │
│  │ stg_events       (materialized=view)                 │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│  STEP 3: Dimension Tables (dbt)                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ dim_date         (materialized=table, full refresh)  │    │
│  │ dim_customers    (materialized=table, full refresh)  │    │
│  │ dim_products     (materialized=table, full refresh)  │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Dimensions run before facts so foreign keys exist.          │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│  STEP 4: Fact Table (dbt)                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ fact_orders  (materialized=incremental)              │    │
│  │                                                       │    │
│  │ Incremental Logic:                                   │    │
│  │ IF first_run:                                        │    │
│  │    Load ALL historical data                          │    │
│  │ ELSE:                                                │    │
│  │    WHERE order_date > MAX(order_date) FROM existing │    │
│  │                                                       │    │
│  │ Joins:                                               │    │
│  │    stg_orders + stg_order_items                      │    │
│  │    → dim_customers (is_current = true)               │    │
│  │    → dim_products                                    │    │
│  │    → dim_date                                        │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│  STEP 5: Analytics Layer (dbt)                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ customer_lifetime_value  (materialized=table)        │    │
│  │                                                       │    │
│  │ Aggregates from fact_orders:                         │    │
│  │  • Sum(line_total) → total_revenue                   │    │
│  │  • Count(order_id) → total_orders                    │    │
│  │  • AVG(line_total) → avg_order_value                 │    │
│  │  • Date math → customer_lifetime_days                │    │
│  │  • Segmentation → value/recency/frequency            │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Surrogate Keys

**Decision**: Use composite surrogate keys generated by `dbt_utils.generate_surrogate_key`.

**Rationale**:

- Reproducible across runs
- Stable identifiers for dimensional modeling
- More robust than auto-increment IDs in distributed systems

**Implementation**:

```sql
-- dim_customers
{{ dbt_utils.generate_surrogate_key(['customer_id', 'segment_start_date']) }}

-- dim_products
{{ dbt_utils.generate_surrogate_key(['product_id']) }}

-- fact_orders
{{ dbt_utils.generate_surrogate_key(['order_id', 'product_id']) }}
```

### 2. SCD Type 2 for Customers

**Decision**: Track customer segment changes over time.

**Rationale**:

- Business requirement to analyze segment transitions
- Historical analysis of customer behavior
- Supports cohort analysis by segment at any point in time

**Implementation**:

- `effective_date`: when the record became active
- `expiration_date`: when the record expired (`9999-12-31` for current)
- `is_current`: boolean flag for filtering

### 3. Incremental Fact Table

**Decision**: Use incremental materialization with time-based filtering.

**Rationale**:

- 66,000+ rows make full refresh slow
- Orders are append-only (no updates after creation)
- Reduces runtime from 45s to 5s for daily updates

**Trade-offs**:

- Staging data must be properly sequenced
- Periodic full refresh may be required for data corrections
- More complex to debug than simple full refresh

### 4. Date Dimension Pre-Generation

**Decision**: Generate four years of dates upfront.

**Rationale**:

- Small table (1,460 rows) with fast generation
- Enables efficient date-based joins
- Pre-calculated attributes improve query performance
- No incremental updates required

### 5. Analytics as Materialized Table

**Decision**: Materialize `customer_lifetime_value` as a table, not a view.

**Rationale**:

- Complex aggregations across the large fact table
- Frequently accessed by dashboards and reports
- Day-old data acceptable for this use case
- Improves query performance by ~10x

---

## Model Dependencies

### Lineage Graph (dbt)

```
sources
  ├── postgres_ecommerce.customers ──► stg_customers ──► dim_customers ─┐
  ├── postgres_ecommerce.orders ─────► stg_orders ─┐                    │
  ├── postgres_ecommerce.order_items ► stg_order_items ┘                │
  │                                                    │                 │
  └─────────────────────────────────► fact_orders ◄───┴─────────────────┤
                                         │   ▲                           │
  postgres_ecommerce.products ──► stg_products ──► dim_products ────────┘
                                         │   ▲
  (generated) ─────────────────────► dim_date ──────────────────────────┘
                                         │
                                         ▼
                              customer_lifetime_value
```

### Execution Order

**Phase 1**: Staging (Views — always run first)

1. stg_customers
2. stg_orders
3. stg_order_items
4. stg_products
5. stg_events

**Phase 2**: Dimensions (Tables — can run in parallel)

6. dim_date
7. dim_customers
8. dim_products

**Phase 3**: Facts (Incremental — depends on dimensions)

9. fact_orders

**Phase 4**: Analytics (Tables — depends on facts)

10. customer_lifetime_value

---

## Data Grain & Cardinality

| Model | Grain | Cardinality | Growth Rate |
|-------|-------|-------------|-------------|
| **dim_date** | One row per day | 1,460 rows | Fixed (4 years) |
| **dim_customers** | One row per customer per segment | ~1,200 rows | ~50 rows/month |
| **dim_products** | One row per product | ~20 rows | ~2 rows/month |
| **fact_orders** | One row per order line item | 66,000+ rows | ~3,000 rows/day |
| **customer_lifetime_value** | One row per customer (current) | ~1,000 rows | ~30 rows/month |

### Join Cardinality Relationships

```
fact_orders (66,000)
├── many-to-one → dim_customers (1,200)     [~55:1 ratio]
├── many-to-one → dim_products (20)         [~3,300:1 ratio]
└── many-to-one → dim_date (1,460)          [~45:1 ratio]
```

---

## Infrastructure Components

### Database Schema Organization

```sql
-- PostgreSQL schema structure
CREATE SCHEMA raw;            -- Airflow ingestion target
CREATE SCHEMA staging;        -- dbt staging views
CREATE SCHEMA analytics;      -- dbt marts (dimensions + facts)
CREATE SCHEMA analytics_dbt_test__audit;  -- dbt test results
```

### dbt Project Structure

```
transform/
├── dbt_project.yml           # Project configuration
├── packages.yml              # dbt packages (utils, expectations)
├── profiles.yml              # Database connections
│
├── models/
│   ├── staging/             # Source → Staging
│   │   ├── orders/
│   │   ├── products/
│   │   └── events/
│   │
│   └── marts/               # Analytics-ready models
│       ├── core/            # Dimensional model
│       │   ├── dim_*.sql
│       │   ├── fact_*.sql
│       │   └── schema.yml
│       │
│       └── analytics/       # Business metrics
│           ├── customer_*.sql
│           └── schema.yml
│
├── macros/                   # Custom SQL macros
├── tests/                    # Custom data tests
├── seeds/                    # CSV reference data
└── target/                   # Compiled SQL & docs
```

---

## Data Quality Framework

### Testing Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Source Tests (sources.yml)                       │
│  - Uniqueness of primary keys                              │
│  - Not null on critical fields                             │
│  - Accepted values for enums                               │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│  Level 2: Staging Tests (schema.yml)                       │
│  - Data type validations                                   │
│  - Business logic flags                                    │
│  - Relationships to sources                                │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│  Level 3: Dimension Tests (marts/core/schema.yml)          │
│  - Surrogate key uniqueness                                │
│  - SCD Type 2 integrity (dates, is_current)                │
│  - Derived field logic                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│  Level 4: Fact Tests (marts/core/schema.yml)               │
│  - Foreign key relationships to all dimensions             │
│  - Measure calculations                                    │
│  - No orphaned records                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│  Level 5: Analytics Tests (marts/analytics/schema.yml)     │
│  - Segmentation logic correctness                          │
│  - Aggregation accuracy                                    │
│  - Business metric validations                             │
└─────────────────────────────────────────────────────────────┘
```
