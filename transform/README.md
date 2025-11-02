# E-Commerce Analytics - dbt Transformation Layer

![dbt Version](https://img.shields.io/badge/dbt-1.6.14-orange)
![Snowflake](https://img.shields.io/badge/Snowflake-Supported-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-blue)

## 📋 Overview

This dbt project transforms raw e-commerce data from S3/PostgreSQL into analytics-ready dimensional models for business intelligence and machine learning applications.

**Project Structure:**
```
transform/
├── models/
│   ├── staging/           # Clean & standardize raw data
│   │   ├── orders/        # Order staging models
│   │   ├── products/      # Product staging models
│   │   └── events/        # Clickstream event models
│   ├── intermediate/      # Business logic transformations
│   └── marts/             # Analytics-ready models
│       ├── core/          # Fact tables (fact_orders)
│       └── dimensions/    # Dimension tables (dim_*)
├── tests/                 # Custom data quality tests
├── macros/                # Reusable SQL functions
├── seeds/                 # Static reference data (CSV)
├── snapshots/             # SCD Type 2 tracking
├── analyses/              # Ad-hoc analytical queries
└── docs/                  # Additional documentation
```

---

## 🎯 Data Model

### Star Schema Architecture

**Grain:** One row per order line item

**Fact Table:**
- `fact_orders` - Transactional order data with measures

**Dimension Tables:**
- `dim_customers` - Customer master with SCD Type 2
- `dim_products` - Product catalog
- `dim_date` - Pre-built date dimension

### Transformation Layers

1. **Staging** (`models/staging/`)
   - Light transformations
   - Column renaming, type casting
   - Materialized as views
   
2. **Intermediate** (`models/intermediate/`)
   - Complex business logic
   - Joins, deduplication, calculations
   - Materialized as views (or tables if needed)
   
3. **Marts** (`models/marts/`)
   - Final analytics models
   - Optimized for query performance
   - Materialized as tables

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9-3.11** with dbt-snowflake installed
2. **Snowflake account** (free trial available)
3. **AWS S3** with raw data (from Week 2 ingestion)

### Installation

```bash
# Navigate to dbt project directory
cd transform

# Install dependencies (if not already installed)
pip install -r ../requirements.txt

# Verify installation
dbt --version
```

### Configuration

1. **Copy profiles template:**
   ```bash
   # Windows
   mkdir %USERPROFILE%\.dbt
   copy profiles.yml.example %USERPROFILE%\.dbt\profiles.yml
   
   # Mac/Linux
   mkdir -p ~/.dbt
   cp profiles.yml.example ~/.dbt/profiles.yml
   ```

2. **Edit `~/.dbt/profiles.yml` with your credentials:**
   ```yaml
   ecommerce_analytics:
     target: dev
     outputs:
       dev:
         type: snowflake
         account: <YOUR_ACCOUNT>      # e.g., xy12345.us-east-1
         user: <YOUR_USERNAME>
         password: <YOUR_PASSWORD>
         role: <YOUR_ROLE>
         warehouse: <YOUR_WAREHOUSE>
         database: <YOUR_DATABASE>
         schema: <YOUR_SCHEMA>
         threads: 4
   ```

3. **Test connection:**
   ```bash
   dbt debug
   ```
   
   Expected output:
   ```
   All checks passed!
   ```

---

## 🛠️ Common Commands

### Development Workflow

```bash
# Run all models
dbt run

# Run specific model
dbt run --select stg_orders

# Run models and downstream dependencies
dbt run --select stg_orders+

# Run models in a specific folder
dbt run --select staging.orders

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve  # Opens in browser at http://localhost:8080

# Full refresh (rebuild all models)
dbt run --full-refresh

# Run in production
dbt run --target prod
```

### Model Selection Syntax

```bash
# By model name
dbt run --select stg_orders

# By path
dbt run --select models/staging/orders

# By tag
dbt run --select tag:daily

# Multiple selectors
dbt run --select stg_orders stg_products

# Exclude models
dbt run --exclude staging

# Graph operators
dbt run --select +stg_orders+    # Model + all parents + all children
dbt run --select +stg_orders     # Model + all parents
dbt run --select stg_orders+     # Model + all children
```

---

## 📊 Model Materialization Strategy

| Layer         | Materialization | Reason                          |
|---------------|-----------------|--------------------------------|
| **Staging**   | View            | Always fresh, low cost         |
| **Intermediate** | View         | Reusable logic, no duplication |
| **Marts - Dims** | Table        | Query performance              |
| **Marts - Facts** | Incremental | Efficient for large datasets   |

### Incremental Model Example

```sql
-- models/marts/core/fact_orders.sql
{{ config(
    materialized='incremental',
    unique_key='order_item_key',
    on_schema_change='fail'
) }}

select * from {{ ref('stg_orders') }}

{% if is_incremental() %}
    where order_date >= (select max(order_date) from {{ this }})
{% endif %}
```

---

## 🧪 Data Quality Testing

### Built-in Tests

```yaml
# models/staging/orders/schema.yml
version: 2

models:
  - name: stg_orders
    description: "Cleaned order data from PostgreSQL"
    columns:
      - name: order_id
        description: "Unique order identifier"
        tests:
          - unique
          - not_null
      
      - name: customer_id
        description: "Foreign key to customers"
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
      
      - name: order_status
        description: "Order status code"
        tests:
          - accepted_values:
              values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
      
      - name: total_amount
        description: "Total order amount"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

### Custom Tests

Create custom tests in `tests/` directory:

```sql
-- tests/assert_revenue_consistency.sql
-- Ensure revenue metrics are consistent across models

select
    order_id,
    sum(line_total) as order_total
from {{ ref('fact_orders') }}
group by order_id
having sum(line_total) < 0  -- Should never happen
```

---

## 📚 Documentation

### Generate Documentation Site

```bash
# Generate docs
dbt docs generate

# Serve locally
dbt docs serve
```

Opens interactive documentation at `http://localhost:8080` with:
- **Lineage graphs** (DAG visualization)
- **Model descriptions** from YAML
- **Column-level documentation**
- **Test results**
- **Source freshness**

### Document Models

```yaml
# models/staging/orders/schema.yml
version: 2

models:
  - name: stg_orders
    description: |
      Staging model for orders from PostgreSQL source.
      
      This model:
      - Cleans column names to snake_case
      - Casts data types appropriately
      - Standardizes timestamps to UTC
      - Filters out test/invalid orders
      
      **Grain:** One row per order
      **Update Frequency:** Daily incremental
    
    columns:
      - name: order_id
        description: "Primary key - unique order identifier"
      
      - name: order_date
        description: "Date the order was placed (UTC)"
```

---

## 🔄 Development Workflow

### Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/add-customer-segmentation

# Make changes to models
# Edit models/marts/dimensions/dim_customers.sql

# Test locally
dbt run --select dim_customers
dbt test --select dim_customers

# Commit and push
git add .
git commit -m "feat: add customer RFM segmentation"
git push origin feature/add-customer-segmentation

# Merge to develop after review
git checkout develop
git merge feature/add-customer-segmentation
```

### CI/CD Integration (Future)

```yaml
# .github/workflows/dbt.yml
name: dbt CI
on: [pull_request]

jobs:
  dbt-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dbt
        run: pip install dbt-snowflake
      - name: Run dbt tests
        run: |
          cd transform
          dbt test --target staging
```

---

## 🎓 Best Practices

### Model Naming Conventions

- **Staging:** `stg_<source>_<entity>.sql`
  - Example: `stg_postgres_orders.sql`
  
- **Intermediate:** `int_<domain>_<description>.sql`
  - Example: `int_orders_enriched.sql`
  
- **Marts - Facts:** `fact_<entity>.sql`
  - Example: `fact_orders.sql`
  
- **Marts - Dimensions:** `dim_<entity>.sql`
  - Example: `dim_customers.sql`

### SQL Style Guide

```sql
-- Use CTEs for readability
with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

final as (
    select
        o.order_id,
        o.order_date,
        c.customer_name,
        o.total_amount
    from orders o
    left join customers c
        on o.customer_id = c.customer_id
)

select * from final
```

### Performance Optimization

1. **Use incremental models** for large fact tables
2. **Cluster on high-cardinality columns** (dates, IDs)
3. **Partition by date** for time-series data
4. **Materialize intermediate models** if reused frequently
5. **Limit data scanned** with effective partitioning

---

## 🐛 Troubleshooting

### Common Issues

**Error: `Could not find profile named 'ecommerce_analytics'`**
```bash
# Solution: Check profiles.yml location
# Should be at ~/.dbt/profiles.yml (not in project directory)
```

**Error: `Database Error 002003 (42S02): SQL compilation error: Object does not exist`**
```bash
# Solution: Ensure source tables exist in Snowflake
# Run data ingestion DAGs first (Week 2)
```

**Error: `Compilation Error: depends on a node named 'ref('stg_orders')' which was not found`**
```bash
# Solution: Check model exists and is in correct directory
# Run: dbt list
```

---

## 📦 Project Dependencies

```yaml
# packages.yml (create if needed)
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  
  - package: calogica/dbt_expectations
    version: 0.9.0
```

Install packages:
```bash
dbt deps
```

---

## 🔐 Security Considerations

- ✅ **Never commit** `profiles.yml` or `.env` files
- ✅ Use **environment variables** for credentials
- ✅ Implement **role-based access control** in Snowflake
- ✅ Use **separate warehouses** for dev/prod
- ✅ Rotate **credentials regularly**
- ✅ Enable **query tags** for auditing

---

## 📈 Project Roadmap

### Week 3: dbt Setup & Staging (Current)
- [x] Project initialization
- [x] Folder structure
- [x] Configuration files
- [ ] Source definitions
- [ ] Staging models
- [ ] Data quality tests

### Week 4: Dimensional Modeling
- [ ] Fact tables (fact_orders)
- [ ] Dimension tables (dim_customers, dim_products, dim_date)
- [ ] SCD Type 2 implementation
- [ ] Incremental loading strategy

### Week 5: Optimization & Testing
- [ ] Query performance tuning
- [ ] Great Expectations integration
- [ ] CI/CD pipeline setup
- [ ] Documentation enhancement

### Week 6: Analytics & Dashboards
- [ ] Metabase integration
- [ ] Business dashboards
- [ ] KPI definitions
- [ ] Final documentation

---

## 📞 Support

**Documentation:** [dbt Docs](https://docs.getdbt.com/)  
**Community:** [dbt Slack](https://www.getdbt.com/community/join-the-community/)  
**Project Repo:** [GitHub](https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform)

---

## 📄 License

This project is created for portfolio and educational purposes.

---

**Last Updated:** November 2, 2024  
**dbt Version:** 1.6.14  
**Target Warehouse:** Snowflake
