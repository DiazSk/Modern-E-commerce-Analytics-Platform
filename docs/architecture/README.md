# Architecture Documentation

**System Design and Technical Decisions**

---

## 📐 Architecture Overview

### High-Level Design

```
┌─────────────┐
│ Data Sources│
│ (API, DB,   │
│  Events)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Ingestion  │
│  (Airflow)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Raw Layer  │
│  (S3)       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Transform Lyr│
│  (dbt)      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Data Marts  │
│ (PostgreSQL)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│BI Dashboards│
│ (Metabase)  │
└─────────────┘
```

### Technology Stack

**Orchestration:** Apache Airflow 2.7.3
**Transformation:** dbt 1.7.4
**Storage:** AWS S3 (Data Lake)
**Warehouse:** PostgreSQL 14
**Data Quality:** Great Expectations 0.18.8
**Visualization:** Metabase
**Infrastructure:** Terraform, Docker Compose

---

## 📁 Contents

### Core Documentation
- **[system-data-flow.md](./system-data-flow.md)** - End-to-end data flow from sources to analytics
- **[dbt-model-specifications.md](./dbt-model-specifications.md)** - Detailed dbt model implementation specs
- **[performance-benchmarks.md](./performance-benchmarks.md)** - Production performance validation results

### [Diagrams](./diagrams/)
Visual architecture representations:
- **architecture.puml** - Detailed system architecture
- **architecture_simple.puml** - High-level overview
- **dimensional_model.puml** - Star schema design
- **dimensional_model_simple.puml** - Simplified data model

### [Infrastructure Screenshots](./infrastructure-screenshots/)
Production deployment evidence:
- **S3 data lake structure** - Bucket organization and partitioning strategy
- **Airflow DAG executions** - Successful pipeline runs
- **dbt lineage diagram** - Data transformation dependencies

### [Decisions](./decisions/)
Architecture Decision Records (ADRs):
- **[001-technology-stack.md](./decisions/001-technology-stack.md)** - Tool selection rationale
- **[002-partitioning-strategy.md](./decisions/002-partitioning-strategy.md)** - Data partitioning approach

---

## 🎯 Key Design Principles

### 1. Medallion Architecture
**Bronze → Silver → Gold**
- **Bronze (Raw):** Immutable landing zone in S3
- **Silver (Staging):** Cleaned, standardized data
- **Gold (Marts):** Business logic, dimensional model

### 2. Star Schema Design
- **1 Fact Table:** `fact_orders` (line-item grain)
- **3 Dimensions:** `dim_customers`, `dim_products`, `dim_date`
- **SCD Type 2:** Customer segment tracking with history

### 3. Incremental Processing
- Fact tables: Incremental materialization
- Dimension tables: Full refresh (small size)
- Date-based partitioning for efficient queries

### 4. Data Quality First
- **146 dbt tests** across all models
- **15 Great Expectations** validations
- **96.3% test pass rate**

---

## 📊 System Metrics

**Data Processed:**
- 1,000 customers
- 5,000 orders
- 10,000 order items
- 50,000 events

**Performance:**
- Query optimization: 67% faster
- Cost reduction: 56% (storage), 85% (compute)
- Data quality: 96.3% pass rate

---

## 🔗 Related Documentation

- [Operations Guide](../operations/)
- [Data Dictionary](../data-catalog/data-dictionary.md)
- [Development Setup](../development/)

---

**Last Updated:** November 10, 2025
