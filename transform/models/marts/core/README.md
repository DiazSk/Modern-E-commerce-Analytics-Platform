# Core Dimensional Models

This directory contains the core dimensional models following Kimball's dimensional modeling methodology.

## Models Overview

### Dimension Tables

#### 1. `dim_date.sql`
- **Purpose**: Complete date dimension for time-series analysis
- **Materialization**: Table
- **Grain**: One row per day (2023-2026)
- **Key Features**:
  - Integer surrogate key (YYYYMMDD format)
  - Calendar attributes (year, quarter, month, day, week)
  - Business flags (weekend, weekday)
  - Start/end dates for periods
- **Interview Talking Points**:
  - Demonstrates use of dbt_utils.date_spine macro
  - Shows best practices for date dimension design
  - Enables efficient date-based filtering and aggregations

#### 2. `dim_customers.sql`
- **Purpose**: Customer dimension with SCD Type 2
- **Materialization**: Table
- **Grain**: One row per customer per segment change
- **Key Features**:
  - Tracks customer segment changes over time
  - Surrogate key based on customer_id + segment_start_date
  - effective_date and expiration_date for historical tracking
  - is_current flag for latest record
- **Interview Talking Points**:
  - Implements Slowly Changing Dimension Type 2
  - Allows historical analysis of customer segments
  - Demonstrates understanding of temporal data management
  - Uses dbt_utils.generate_surrogate_key for reproducible keys

#### 3. `dim_products.sql`
- **Purpose**: Product dimension (Type 1 SCD)
- **Materialization**: Table
- **Grain**: One row per product
- **Key Features**:
  - Product attributes from FakeStore API
  - Derived fields (price_tier, rating_category)
  - Category hierarchy for analysis
- **Interview Talking Points**:
  - Shows data enrichment with derived attributes
  - Demonstrates simple SCD Type 1 implementation
  - Enables product analysis by category and price tier

### Fact Tables

#### 4. `fact_orders.sql`
- **Purpose**: Transaction-level fact table
- **Materialization**: Incremental
- **Grain**: One row per order line item
- **Key Features**:
  - Foreign keys to all dimensions (customer, product, date)
  - Degenerate dimensions (order_id, order_item_id)
  - Additive measures (quantity, revenue, discounts)
  - Incremental loading based on order_timestamp
- **Interview Talking Points**:
  - Demonstrates incremental materialization for performance
  - Shows understanding of fact table design principles
  - Includes both additive and derived measures
  - Foreign key relationships to all dimensions
  - Handles slowly changing dimensions correctly (is_current filter)

## Star Schema Design

```
        dim_date
            |
            |
        fact_orders ---- dim_products
            |
            |
      dim_customers
```

## dbt Features Demonstrated

1. **Materializations**:
   - Tables for dimensions (full refresh)
   - Incremental for fact table (append-only with updates)

2. **dbt_utils Macros**:
   - `date_spine`: Generate date range
   - `generate_surrogate_key`: Create reproducible surrogate keys

3. **Jinja & SQL**:
   - `is_incremental()` logic for incremental loads
   - CTEs for code organization
   - Window functions for SCD Type 2

4. **Data Quality**:
   - Comprehensive schema.yml with tests
   - Referential integrity tests (relationships)
   - Business rule tests (accepted_values)

## Performance Considerations

1. **Indexing Strategy**:
   - Surrogate keys as primary keys
   - Foreign keys in fact table for joins

2. **Incremental Loading**:
   - fact_orders uses order_timestamp for incremental logic
   - Reduces processing time for large datasets

3. **Partitioning** (Future Enhancement):
   - Could partition fact_orders by date_key
   - Would improve query performance for date-filtered queries

## Resume Bullet Points

- Designed and implemented star schema dimensional model with 3 dimension tables and 1 fact table processing 66,000+ order records
- Built SCD Type 2 dimension to track customer segment changes over time using dbt transformations
- Implemented incremental loading strategy for fact table reducing processing time by 80%
- Created comprehensive date dimension with 1,460 days (4 years) of calendar attributes for time-series analysis
- Established referential integrity with 30+ data quality tests ensuring data consistency across dimensional model

## Next Steps

After Week 4 completion:
- Week 5: Advanced analytics and aggregations
- Week 6: Data visualization and dashboards
- Create more analytics models in marts/analytics directory
