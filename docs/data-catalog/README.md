# Data Catalog

**Schema Documentation and Data Dictionary**

---

## 📖 Overview

Comprehensive documentation of all data tables, columns, relationships, and business rules in the Modern E-Commerce Analytics Platform.

---

## 📋 Contents

### [Data Dictionary](./data-dictionary.md)
Complete schema reference including:
- **5 Core Tables** (customers, products, orders, order items, events)
- **Column Specifications** (types, constraints, examples)
- **Relationships** (foreign keys, joins)
- **Business Rules** (segmentation logic, calculations)
- **Common Queries** (reference examples)

### [Data Quality Audit](./data-quality-audit.md)
Quality validation results:
- **96.3% pass rate** across all tests
- **Great Expectations** validation suite
- **Performance benchmarks** and audit trails

---

## 🗂️ Schema Overview

### Dimensional Model (Star Schema)

```
        dim_customers (SCD Type 2)
              │
              │ 1:N
              ▼
         fact_orders ────────▶ dim_date
              │
              │ 1:N
              ▼
      fact_order_items
              │
              │ N:1
              ▼
         dim_products
```

### Grain Definitions

**Fact Tables:**
- `fact_orders` - One row per order
- `fact_order_items` - One row per order × product
- `fact_events` - One row per user interaction

**Dimension Tables:**
- `dim_customers` - One row per customer per segment period
- `dim_products` - One row per product
- `dim_date` - One row per calendar date

---

## 📊 Data Volumes

| Table | Records | Growth Rate |
|-------|---------|-------------|
| dim_customers | 1,000 | Low (10-20% YoY) |
| dim_products | 200 | Low (5-10% YoY) |
| fact_orders | 5,000 | High (~5K/day) |
| fact_order_items | 10,000 | High (~10K/day) |
| fact_events | 50,000 | Very High (~50K/day) |

---

## 🔍 Data Lineage

### Source to Target

**Products:**
```
API (fakestoreapi.com) → Airflow DAG → S3 Raw → dbt Staging → dim_products
```

**Orders:**
```
PostgreSQL Source → Airflow DAG → S3 Raw → dbt Staging → fact_orders
```

**Events:**
```
CSV Files → Airflow DAG → S3 Raw → dbt Staging → fact_events
```

---

## 🎯 Quick Reference

### Most Queried Tables
1. `fact_orders` - Revenue analysis
2. `dim_customers` - Customer segmentation
3. `dim_products` - Product performance
4. `fact_events` - Behavioral analysis

### Common Joins
```sql
-- Orders with customer info
fact_orders fo
JOIN dim_customers dc ON fo.customer_key = dc.customer_key
  AND dc.is_current = TRUE

-- Order items with products
fact_order_items foi
JOIN dim_products dp ON foi.product_key = dp.product_key
```

### Key Metrics
- **Total Revenue:** $692,072.36
- **Average Order Value:** $138.41
- **Active Customers:** 1,000
- **Product Catalog:** 200 items

---

## 📝 Data Quality

**Test Coverage:**
- dbt tests: 146 tests across all models
- Great Expectations: 15 validations on fact_orders
- Pass rate: 96.3%

**Known Issues:**
- None currently tracked

---

## 🔗 Related Documentation

- [Architecture Overview](../architecture/)
- [dbt Models](../../transform/models/)
- [BI Dashboards](../analytics/metabase/)

---

**Last Updated:** November 10, 2025
**Auto-Generated:** Consider using `dbt docs generate` for automated lineage
