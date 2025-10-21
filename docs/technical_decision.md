# Technical Decisions Document

> **Purpose:** Document key architectural and technology choices for the Modern E-Commerce Analytics Platform

**Last Updated:** January 20, 2025  
**Version:** 1.0  
**Author:** [Your Name]

---

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [Architecture Decisions](#architecture-decisions)
3. [Data Modeling Decisions](#data-modeling-decisions)
4. [Infrastructure Decisions](#infrastructure-decisions)
5. [Security Decisions](#security-decisions)
6. [Cost Optimization Decisions](#cost-optimization-decisions)
7. [Future Considerations](#future-considerations)

---

## Technology Stack

### Orchestration: Apache Airflow

**Decision:** Use Apache Airflow for workflow orchestration

**Alternatives Considered:**
- Prefect
- Dagster
- Luigi
- AWS Step Functions

**Rationale:**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Industry adoption | High | 9/10 | De facto standard in data engineering |
| Learning curve | Medium | 7/10 | Well-documented, large community |
| Features | High | 9/10 | DAGs, retries, monitoring, alerting |
| Cost | High | 10/10 | Free, open-source |
| Portfolio value | High | 10/10 | FAANG companies use Airflow heavily |

**Key Benefits:**
- Python-based DAG definitions (familiar language)
- Built-in UI for monitoring
- Strong retry/error handling mechanisms
- Widely recognized by employers

**Trade-offs:**
- Steeper learning curve than some alternatives
- Requires infrastructure (Docker setup needed)

---

### Transformation: dbt (Data Build Tool)

**Decision:** Use dbt for SQL-based transformations

**Alternatives Considered:**
- Spark (PySpark)
- Plain SQL scripts
- Stored procedures
- Pandas transformations

**Rationale:**

**Why dbt over Spark?**
```
Spark:
+ Handles huge scale (PB+)
+ In-memory processing
- Overkill for batch analytics on < 1TB data
- Steeper learning curve
- More infrastructure complexity

dbt:
+ Perfect for batch SQL transformations
+ Built-in testing framework
+ Automatic documentation generation
+ Version control friendly
+ Industry standard for analytics engineering
```

**Key Benefits:**
- **Modularity:** Reusable SQL models
- **Testing:** Built-in data quality tests
- **Documentation:** Auto-generated data lineage
- **Version Control:** Git-based workflow
- **Incremental Models:** Efficient processing of only new data

**Trade-offs:**
- SQL-only (not suitable for complex ML transformations)
- Requires data warehouse target

---

### Data Warehouse: Snowflake

**Decision:** Use Snowflake as the data warehouse

**Alternatives Considered:**
- Google BigQuery
- AWS Redshift
- PostgreSQL (on-prem)
- Databricks SQL

**Rationale:**

| Feature | Snowflake | BigQuery | Redshift |
|---------|-----------|----------|----------|
| **Separation of compute/storage** | ✅ Best | ✅ Good | ❌ Coupled |
| **Auto-scaling** | ✅ Yes | ✅ Yes | ⚠️ Manual |
| **Zero-copy cloning** | ✅ Yes | ❌ No | ❌ No |
| **Free trial** | ✅ $400 credit | ✅ $300 credit | ⚠️ Limited |
| **Semi-structured data (JSON)** | ✅ Excellent | ✅ Excellent | ⚠️ Limited |
| **Query performance** | ✅ Excellent | ✅ Excellent | ✅ Good |
| **Cost (after free tier)** | $$$ | $$ | $$ |
| **Resume/suspend** | ✅ Auto | N/A | ⚠️ Manual |

**Decision: Snowflake**

**Key Reasons:**
1. **Zero-copy cloning:** Instant dev/test environments
2. **Separation of compute/storage:** Scale independently
3. **Auto-suspend:** Stops billing when idle (5 min)
4. **Portfolio appeal:** Snowflake skills highly valued
5. **Free trial:** $400 credit sufficient for 6-week project

**Trade-offs:**
- More expensive than BigQuery long-term
- Not fully serverless (need to manage warehouse size)

---

### Storage: AWS S3

**Decision:** Use AWS S3 as the data lake

**Alternatives Considered:**
- Google Cloud Storage (GCS)
- Azure Blob Storage
- HDFS (Hadoop)

**Rationale:**
- Industry standard for data lakes
- Cost-effective ($0.023/GB/month STANDARD)
- Mature lifecycle management
- Integrates with all major tools (Airflow, dbt, Snowflake)
- Free tier: 5GB for 12 months

**Key Features Used:**
- Versioning for data recovery
- Lifecycle policies for cost optimization
- Server-side encryption for security
- Partitioned structure (YYYY/MM/DD)

---

## Architecture Decisions

### AD-001: Batch vs. Streaming

**Decision:** Batch processing with daily incremental loads

**Context:**
- E-commerce analytics (not real-time dashboards)
- Data sources update daily
- Cost constraints

**Alternatives:**
- Real-time streaming (Kafka + Spark Structured Streaming)
- Micro-batching (every 5 minutes)

**Rationale:**
```
Business Requirements:
- Dashboards updated daily ✅
- Reports generated overnight ✅
- Real-time alerts not required ✅

Cost Comparison (monthly):
Batch (Airflow + S3 + Snowflake):
- S3 storage: $2
- Snowflake compute: $5-10 (with auto-suspend)
- Total: ~$7-12/month

Streaming (Kafka + Spark + Kinesis):
- Kinesis: $15/shard/month
- Spark cluster: $50-100/month
- Total: ~$65-115/month

Savings: $53-103/month (88% cheaper)
```

**Decision:** Batch processing is sufficient and cost-effective

---

### AD-002: Medallion Architecture (Bronze/Silver/Gold)

**Decision:** Implement 3-layer medallion architecture

**Layers:**
1. **Bronze (Raw):** S3 raw layer - immutable landing zone
2. **Silver (Staging):** dbt staging models - cleaned/standardized
3. **Gold (Marts):** dbt marts - business logic/dimensional model

**Rationale:**
- **Separation of concerns:** Raw → Clean → Business logic
- **Reprocessing:** Can re-transform from bronze if needed
- **Data lineage:** Clear path from source to consumption
- **Industry standard:** Databricks/Snowflake best practice

**Alternative (2-layer):**
```
Raw → Mart (skip staging)

Pros: Simpler, fewer layers
Cons: Mixes cleaning with business logic, harder to debug
```

**Decision:** 3-layer provides better maintainability

---

### AD-003: Incremental vs. Full Refresh

**Decision:** Incremental loading for fact tables, full refresh for dimensions

**Rationale:**

**Fact Tables (fact_orders):**
```sql
-- Incremental strategy
{{ config(
    materialized='incremental',
    unique_key='order_key'
) }}

SELECT * FROM {{ ref('stg_orders') }}
{% if is_incremental() %}
    WHERE order_timestamp > (SELECT MAX(order_timestamp) FROM {{ this }})
{% endif %}
```

**Why incremental?**
- Fact tables grow indefinitely (millions of rows)
- Full refresh = rescan entire table every run (expensive!)
- Incremental = process only new records (fast!)

**Performance Impact:**
```
Full Refresh:
- Runtime: 15 minutes
- Data processed: 10GB
- Cost: $0.05/run

Incremental:
- Runtime: 2 minutes
- Data processed: 100MB (yesterday's data)
- Cost: $0.002/run

Daily runs savings: $0.048 × 365 = $17.52/year
```

**Dimension Tables (dim_customers, dim_products):**
```sql
{{ config(
    materialized='table'  -- Full refresh
) }}
```

**Why full refresh?**
- Small tables (1K-10K rows)
- SCD Type 2 logic easier with full refresh
- Runtime negligible (< 30 seconds)
- Cost negligible

---

## Data Modeling Decisions

### DM-001: Star Schema vs. Snowflake Schema

**Decision:** Star schema with denormalization

**Comparison:**
```
Star Schema:
dim_customers → fact_orders → dim_products

Snowflake Schema:
dim_customer_segments → dim_customers → fact_orders
dim_categories → dim_products → fact_orders
```

**Rationale:**

**Star Schema Benefits:**
- Fewer joins = better BI tool performance
- Simpler for business users to understand
- Standard for data warehouses (Kimball methodology)
- Acceptable denormalization (storage is cheap)

**Snowflake Schema Benefits:**
- More normalized (less redundancy)
- Better for operational databases

**Decision:** Star schema - optimized for analytics, not OLTP

---

### DM-002: SCD Type 2 for Customers

**Decision:** Slowly Changing Dimension Type 2 for customer segments

**Alternatives:**
- **SCD Type 1:** Overwrite (lose history)
- **SCD Type 2:** Track history (multiple rows per customer)
- **SCD Type 3:** Limited history (additional columns)

**Rationale:**

**Business Questions:**
- "What were platinum customers buying 6 months ago?"
- "How does purchasing behavior change after segment upgrade?"
- "Calculate accurate customer lifetime value by segment"

**Implementation:**
```sql
customer_id | customer_key | segment  | effective_date | expiration_date | is_current
1001        | 1            | bronze   | 2024-01-01     | 2024-06-01      | FALSE
1001        | 2            | silver   | 2024-06-01     | 9999-12-31      | TRUE
```

**Trade-offs:**
- Storage: 10-20% increase (acceptable)
- Query complexity: Slightly more complex (use is_current flag)
- Historical analysis: Enabled ✅

**Decision:** SCD Type 2 - business value > implementation complexity

---

### DM-003: Grain of Fact Table

**Decision:** Order line item grain (order_id + product_id)

**Alternatives:**
- **Order header grain:** One row per order (lose product detail)
- **Line item grain:** One row per order × product ✅
- **Event grain:** One row per customer interaction (too granular)

**Rationale:**

**Business Questions:**
- "Which products are frequently bought together?"
- "What's the average quantity per product per order?"
- "Product performance by customer segment?"

**All require line-item detail!**

**Impact on Storage:**
```
Order header grain:
- 5,000 orders/day × 365 days = 1.8M rows/year
- Storage: ~500MB/year

Line item grain:
- 5,000 orders/day × 2.5 products/order × 365 = 4.5M rows/year
- Storage: ~1.2GB/year

Incremental cost: 700MB/year = $0.02/month
Business value: Enables product-level analytics ✅
```

**Decision:** Line-item grain - minimal cost for significant value

---

## Infrastructure Decisions

### INF-001: Infrastructure as Code (Terraform)

**Decision:** Use Terraform for all AWS infrastructure

**Alternatives:**
- AWS CLI scripts
- AWS CloudFormation
- Manual console creation
- Pulumi

**Rationale:**
| Factor | Terraform | CloudFormation | Manual |
|--------|-----------|----------------|--------|
| Reproducibility | ✅ Perfect | ✅ Perfect | ❌ Manual |
| Multi-cloud | ✅ Yes | ❌ AWS only | ❌ N/A |
| Version control | ✅ Yes | ✅ Yes | ❌ No |
| State management | ✅ Built-in | ✅ AWS-managed | ❌ No |
| Learning value | ✅ High | ⚠️ Medium | ❌ Low |
| Portability | ✅ High | ❌ AWS-locked | ❌ No |

**Key Benefits:**
- **Reproducibility:** `terraform apply` = identical infrastructure
- **Version control:** Git tracks all changes
- **Documentation:** Code IS documentation
- **Portfolio value:** Terraform highly sought skill

**Decision:** Terraform - industry standard IaC tool

---

### INF-002: Docker Compose for Local Development

**Decision:** Docker Compose for local orchestration

**Rationale:**
- **One-command setup:** `docker-compose up`
- **Environment consistency:** Dev = Prod (minus scale)
- **Easy onboarding:** New team members productive in minutes
- **No local installs:** Everything containerized

**Services:**
```yaml
services:
  - postgres (source database)
  - airflow-webserver
  - airflow-scheduler
  - airflow-worker
  - metabase (BI tool)
```

**Alternative (local installs):**
```
Install Python 3.11 ✅
Install PostgreSQL ✅
Install Airflow ❌ (complex dependencies)
Install Metabase ✅
Configure connections ❌ (error-prone)

vs.

docker-compose up ✅ (works first try)
```

**Decision:** Docker Compose - simplicity + portability

---

## Security Decisions

### SEC-001: S3 Bucket Security

**Decision:** Defense in depth approach

**Layers:**
1. **Private ACLs:** Default deny
2. **Public access block:** Block all 4 public access types
3. **Server-side encryption:** AES256 on all objects
4. **Versioning:** Protect against accidental deletion
5. **Access logging:** Audit trail

**Rationale:**
- If one layer fails, others still protect data
- Industry best practice (AWS Well-Architected Framework)
- Compliance-ready (GDPR, HIPAA compatible)

**Cost of security:**
- Versioning: ~10% storage increase
- Encryption: No additional cost (SSE-S3)
- Logging: ~1% of main bucket size

**Decision:** Security > minimal cost increase

---

### SEC-002: Credentials Management

**Decision:** No credentials in Git, use environment variables

**Implementation:**
```
✅ .env files (gitignored)
✅ AWS IAM roles (where possible)
✅ Airflow Connections (encrypted in DB)
❌ Never hardcode credentials in code
```

**.gitignore:**
```
*.env
.env.*
credentials.json
profiles.yml
aws_credentials.txt
```

**Rationale:**
- Security: Prevent credential leaks
- Portfolio: Shows security awareness
- Best practice: 12-factor app methodology

---

## Cost Optimization Decisions

### COST-001: S3 Lifecycle Policies

**Decision:** Automated storage tiering

**Strategy:**
```
Day 0-90:   STANDARD ($0.023/GB/month)
Day 90-180: STANDARD_IA ($0.0125/GB/month) - 46% cheaper
Day 180+:   GLACIER_IR ($0.004/GB/month) - 83% cheaper
```

**Rationale:**
```
Data Access Patterns:
- Recent data (< 3 months): Frequent access (daily queries)
- Historical data (3-6 months): Occasional access (monthly reports)
- Archive data (> 6 months): Rare access (compliance/audit)

Cost Impact (100GB/month ingestion rate):
Year 1:
- Without lifecycle: $276/year
- With lifecycle: $145/year
- Savings: $131/year (47%)

Year 2 (cumulative):
- Without lifecycle: $552/year
- With lifecycle: $234/year
- Savings: $318/year (58%)
```

**Decision:** Lifecycle policies - automatic cost reduction

---

### COST-002: Snowflake Auto-Suspend

**Decision:** Auto-suspend warehouse after 5 minutes idle

**Configuration:**
```sql
ALTER WAREHOUSE COMPUTE_WH SET 
  AUTO_SUSPEND = 300  -- 5 minutes
  AUTO_RESUME = TRUE;
```

**Rationale:**
```
Billing Scenarios:

Always On (24/7):
- Runtime: 720 hours/month
- Cost: $2/credit × 1 credit/hour × 720 = $1,440/month

Manual Start/Stop (8 hours/day, 5 days/week):
- Runtime: 160 hours/month
- Cost: $2/credit × 1 credit/hour × 160 = $320/month

Auto-Suspend (5 min idle):
- Actual usage: ~20 hours/month (dev workload)
- Cost: $2/credit × 1 credit/hour × 20 = $40/month

Savings: $1,400/month (97% vs. always-on!)
```

**Decision:** Auto-suspend - massive cost reduction

---

## Future Considerations

### FC-001: Real-time Streaming Layer

**Current:** Batch processing (daily)  
**Future:** Add streaming for real-time dashboards

**Trigger:** Business requirement for real-time metrics

**Technologies to add:**
- Apache Kafka or AWS Kinesis
- Spark Structured Streaming
- Real-time dashboard (Grafana)

**Estimated effort:** 2-3 weeks  
**Estimated cost increase:** +$50-100/month

---

### FC-002: Machine Learning Integration

**Current:** Analytics only  
**Future:** ML feature store + prediction models

**Use cases:**
- Customer churn prediction
- Product recommendation engine
- Dynamic pricing optimization

**Technologies to add:**
- MLflow (experiment tracking)
- Feature store (Feast or Tecton)
- Model serving (SageMaker or Databricks)

**Estimated effort:** 4-6 weeks  
**Estimated cost increase:** +$30-80/month

---

### FC-003: Data Catalog

**Current:** dbt docs for data lineage  
**Future:** Enterprise data catalog

**Trigger:** Growing team size (5+ data engineers)

**Technologies:**
- DataHub (open-source)
- Amundsen
- AWS Glue Catalog

**Benefits:**
- Centralized metadata
- Data discovery
- Automated lineage

**Estimated effort:** 1-2 weeks

---

## Appendix: Decision Log

| ID | Date | Decision | Status | Owner |
|----|------|----------|--------|-------|
| AD-001 | 2025-01-20 | Batch vs. Streaming | Approved | [Your Name] |
| AD-002 | 2025-01-20 | Medallion Architecture | Approved | [Your Name] |
| DM-001 | 2025-01-20 | Star Schema | Approved | [Your Name] |
| INF-001 | 2025-01-20 | Terraform IaC | Approved | [Your Name] |

---

**Document Owner:** [Your Name]  
**Review Cycle:** Weekly during project, quarterly after launch  
**Next Review:** 2025-01-27