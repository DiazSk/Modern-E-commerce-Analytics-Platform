# dbt Transformation Layer Setup Guide

## 🎯 Overview

This directory contains the dbt (data build tool) transformation layer for the Modern E-Commerce Analytics Platform. dbt transforms raw ingested data into analytics-ready dimensional models.

**Status:** Week 3 - dbt Setup Complete ✅
**Last Updated:** November 2, 2025

---

## 📁 Project Structure

```
transform/
├── analyses/           # Ad-hoc analytical queries
├── macros/            # Reusable SQL macros
├── models/            # dbt transformation models
│   ├── staging/       # Layer 1: Raw data cleaning
│   │   ├── orders/
│   │   ├── products/
│   │   └── events/
│   ├── intermediate/  # Layer 2: Business logic
│   └── marts/         # Layer 3: Analytics-ready models
│       ├── core/      # Fact tables
│       └── dimensions/ # Dimension tables
├── seeds/             # Static reference data (CSV)
├── snapshots/         # SCD Type 2 historical tracking
├── tests/             # Custom data quality tests
├── dbt_project.yml    # Main project configuration
├── packages.yml       # dbt package dependencies
└── profiles.yml.example # Connection template
```

---

## 🏗️ Three-Layer Architecture

### **1. Staging Layer (`models/staging/`)**
- **Purpose:** Light transformations, type casting, column renaming
- **Materialization:** Views (always fresh, low cost)
- **Naming:** `stg_<source>_<entity>.sql`
- **Example:** `stg_orders_orders.sql`, `stg_products_products.sql`

**Key Principles:**
- One source = one staging model
- Minimal business logic
- Column renaming for consistency
- Type casting and parsing
- No joins at this layer

---

### **2. Intermediate Layer (`models/intermediate/`)**
- **Purpose:** Complex transformations, joins, aggregations
- **Materialization:** Views (unless performance requires tables)
- **Naming:** `int_<domain>_<description>.sql`
- **Example:** `int_orders_deduplicated.sql`, `int_customers_aggregated.sql`

**Key Principles:**
- Bridge between staging and marts
- Implement business logic
- Deduplication and data quality
- Can join multiple staging models
- Not exposed to end users

---

### **3. Marts Layer (`models/marts/`)**
- **Purpose:** Analytics-ready dimensional models for BI
- **Materialization:** Tables (optimized for query performance)
- **Naming:** `fact_<entity>.sql`, `dim_<entity>.sql`
- **Example:** `fact_orders.sql`, `dim_customers.sql`

**Subfolders:**
- `core/` - Fact tables (transactional data)
- `dimensions/` - Dimension tables (descriptive attributes)

**Key Principles:**
- Final models for BI tools
- Optimized for query performance
- Implement star schema design
- Include SCD Type 2 where needed
- Comprehensive documentation

---

## 🔧 Setup Instructions

### **Prerequisites**
- Python 3.9+ with dbt-core and dbt-snowflake installed
- Snowflake account (or PostgreSQL for local testing)
- AWS S3 access (raw data storage)

---

### **Step 1: Configure Snowflake Connection**

#### **Create Snowflake Resources**

Run these SQL commands in Snowflake (as ACCOUNTADMIN):

```sql
-- Create warehouse for dbt
CREATE WAREHOUSE IF NOT EXISTS DBT_WH
  WITH WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- Create development database
CREATE DATABASE IF NOT EXISTS ECOMMERCE_DEV;

-- Create schema
CREATE SCHEMA IF NOT EXISTS ECOMMERCE_DEV.DBT_DEV;

-- Create role
CREATE ROLE IF NOT EXISTS DBT_ROLE;

-- Grant permissions
GRANT USAGE ON WAREHOUSE DBT_WH TO ROLE DBT_ROLE;
GRANT ALL ON DATABASE ECOMMERCE_DEV TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA ECOMMERCE_DEV.DBT_DEV TO ROLE DBT_ROLE;

-- Assign role to user
GRANT ROLE DBT_ROLE TO USER <YOUR_USERNAME>;
```

---

#### **Configure profiles.yml**

**Linux/Mac:**
```bash
mkdir -p ~/.dbt
cp profiles.yml.example ~/.dbt/profiles.yml
nano ~/.dbt/profiles.yml
```

**Windows:**
```powershell
mkdir $env:USERPROFILE\.dbt -Force
Copy-Item profiles.yml.example $env:USERPROFILE\.dbt\profiles.yml
notepad $env:USERPROFILE\.dbt\profiles.yml
```

Edit `~/.dbt/profiles.yml` with your Snowflake credentials:

```yaml
ecommerce_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: xy12345.us-east-1  # Your Snowflake account
      user: your_username
      password: your_password
      role: DBT_ROLE
      warehouse: DBT_WH
      database: ECOMMERCE_DEV
      schema: DBT_DEV
      threads: 4
```

---

### **Step 2: Install dbt Packages**

```bash
cd transform/
dbt deps
```

This installs:
- `dbt_utils` - Utility macros (surrogate keys, unions, etc.)
- `codegen` - Auto-generate YAML boilerplate
- `dbt_expectations` - Advanced data quality tests

---

### **Step 3: Test Connection**

```bash
dbt debug
```

**Expected output:**
```
All checks passed!
```

If you see errors, verify:
- Snowflake credentials in `~/.dbt/profiles.yml`
- Network connectivity to Snowflake
- Role permissions in Snowflake

---

### **Step 4: Compile Models (Dry Run)**

```bash
# Compile without running (validates SQL syntax)
dbt compile
```

Check `target/compiled/` for compiled SQL files.

---

### **Step 5: Run dbt Models**

```bash
# Run all models
dbt run

# Run specific model
dbt run --select stg_orders

# Run with full refresh (drop and recreate)
dbt run --full-refresh

# Run models matching tag
dbt run --select tag:staging
```

---

### **Step 6: Run Tests**

```bash
# Run all tests
dbt test

# Test specific model
dbt test --select stg_orders

# Test staging layer only
dbt test --select tag:staging
```

---

### **Step 7: Generate Documentation**

```bash
# Generate docs site
dbt docs generate

# Serve docs locally
dbt docs serve
```

Opens documentation at `http://localhost:8080` with:
- Data lineage graphs
- Column descriptions
- Test results
- Model relationships

---

## 📦 Installed Packages

### **dbt_utils** (v1.1.1)
Common macros for data transformation.

**Examples:**
```sql
-- Generate surrogate key
{{ dbt_utils.generate_surrogate_key(['order_id', 'product_id']) }}

-- Union multiple tables
{{ dbt_utils.union_relations([ref('table1'), ref('table2')]) }}

-- Create date spine
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2023-01-01' as date)",
    end_date="cast('2025-12-31' as date)"
) }}
```

---

### **codegen** (v0.11.0)
Auto-generate dbt boilerplate code.

**Examples:**
```sql
-- Generate source YAML from database
{{ codegen.generate_source('raw_schema') }}

-- Generate base model
{{ codegen.generate_base_model('source_name', 'table_name') }}
```

---

### **dbt_expectations** (v0.9.0)
Advanced data quality tests.

**Examples:**
```yaml
# In schema.yml
models:
  - name: stg_orders
    columns:
      - name: order_amount
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 10000
      - name: order_date
        tests:
          - dbt_expectations.expect_column_values_to_be_of_type:
              column_type: date
```

---

## 🎯 Model Development Workflow

### **1. Create Staging Model**

File: `models/staging/orders/stg_orders_orders.sql`

```sql
with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        id as order_id,
        customer_id,
        order_date,
        order_amount,
        status
    from source
)

select * from renamed
```

### **2. Document Model**

File: `models/staging/orders/schema.yml`

```yaml
version: 2

models:
  - name: stg_orders_orders
    description: Staging model for orders from PostgreSQL
    columns:
      - name: order_id
        description: Unique order identifier
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
```

### **3. Run and Test**

```bash
dbt run --select stg_orders_orders
dbt test --select stg_orders_orders
```

---

## 🔍 Common Commands

```bash
# Development
dbt compile                    # Validate SQL syntax
dbt run                        # Execute models
dbt test                       # Run data quality tests
dbt build                      # Run + test in one command

# Specific selections
dbt run --select stg_orders    # Single model
dbt run --select staging.*     # All staging models
dbt run --select +fact_orders  # Model + upstream deps
dbt run --select tag:daily     # Models with 'daily' tag

# Full refresh
dbt run --full-refresh         # Drop and recreate all tables

# Documentation
dbt docs generate              # Create docs
dbt docs serve                 # View docs at localhost:8080

# Debugging
dbt debug                      # Test connection
dbt show --select stg_orders   # Preview model output
dbt run-operation <macro>      # Execute macro
```

---

## 📊 Materialization Strategies

| Strategy | Use Case | Storage | Performance |
|----------|----------|---------|-------------|
| **view** | Staging models | Minimal | Fast to build |
| **table** | Marts, dimensions | Medium | Fast to query |
| **incremental** | Large fact tables | Efficient | Best of both |
| **ephemeral** | CTE-like reuse | None | N/A |

---

## ✅ Data Quality Framework

### **Generic Tests** (Built-in)
- `unique` - No duplicate values
- `not_null` - No NULL values
- `accepted_values` - Value in allowed list
- `relationships` - Foreign key validation

### **Custom Tests** (Custom SQL)
File: `tests/assert_positive_revenue.sql`

```sql
-- Revenue should never be negative
select *
from {{ ref('fact_orders') }}
where revenue < 0
```

### **dbt Expectations Tests**
Advanced statistical and data quality tests.

---

## 🔒 Security Best Practices

**DO:**
- ✅ Store `profiles.yml` in home directory only
- ✅ Use environment variables for credentials
- ✅ Use key-pair authentication for production
- ✅ Separate dev/staging/prod warehouses
- ✅ Limit role permissions (least privilege)

**DON'T:**
- ❌ Commit `profiles.yml` to Git
- ❌ Share credentials via email/Slack
- ❌ Use ACCOUNTADMIN for dbt
- ❌ Hardcode passwords in dbt_project.yml

---

## 🚨 Troubleshooting

### **Issue: "Compilation Error"**
- Check SQL syntax in model
- Verify `ref()` and `source()` references
- Run `dbt compile` to see detailed errors

### **Issue: "Database Error"**
- Test connection: `dbt debug`
- Verify Snowflake credentials
- Check warehouse is running

### **Issue: "Permission Denied"**
- Verify role has USAGE on warehouse
- Grant CREATE TABLE on schema
- Check database ownership

### **Issue: "Models Not Found"**
- Ensure model in correct directory
- Check `dbt_project.yml` model-paths
- Verify file extension is `.sql`

---

## 📚 Resources

**Official Documentation:**
- [dbt Docs](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [dbt Discourse Community](https://discourse.getdbt.com/)

**Package Documentation:**
- [dbt_utils](https://hub.getdbt.com/dbt-labs/dbt_utils/latest/)
- [codegen](https://hub.getdbt.com/dbt-labs/codegen/latest/)
- [dbt_expectations](https://hub.getdbt.com/calogica/dbt_expectations/latest/)

**Snowflake + dbt:**
- [Snowflake dbt Profile](https://docs.getdbt.com/reference/warehouse-profiles/snowflake-profile)
- [Snowflake Optimization](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions.html)

---

## 🎓 Next Steps (Week 3+)

- [ ] **Week 3 Feature 2:** Configure source connections to S3
- [ ] **Week 3 Feature 3:** Build staging models (orders, products, events)
- [ ] **Week 3 Feature 4:** Implement data quality tests
- [ ] **Week 4:** Intermediate transformations and dimensional modeling
- [ ] **Week 5:** Query optimization and performance tuning
- [ ] **Week 6:** BI dashboards and final documentation

---

**Project:** Modern E-Commerce Analytics Platform
**Developer:** Zaid Shaikh
**Last Updated:** November 2, 2025
**Status:** Week 3 - dbt Setup Complete ✅
