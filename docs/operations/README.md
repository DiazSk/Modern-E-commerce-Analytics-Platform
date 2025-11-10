# Operations Documentation

**Runbooks and Operational Procedures**

---

## 🎯 Overview

This section contains operational runbooks, setup guides, and data ingestion procedures for the Modern E-Commerce Analytics Platform.

---

## 📂 Contents

### [Runbooks](./runbooks/)
Step-by-step operational procedures:
- **[airflow-setup.md](./runbooks/airflow-setup.md)** - Airflow configuration and connections
- **[great-expectations-reference.md](./runbooks/great-expectations-reference.md)** - Data quality validation commands

### [Data Ingestion](./data-ingestion/)
DAG-specific ingestion guides:
- **[ingest-api-products.md](./data-ingestion/ingest-api-products.md)** - API product data pipeline
- **[ingest-postgres-orders.md](./data-ingestion/ingest-postgres-orders.md)** - PostgreSQL order data pipeline
- **[ingest-clickstream-events.md](./data-ingestion/ingest-clickstream-events.md)** - Event streaming pipeline

---

## 🚀 Quick Start

1. **Setup Infrastructure**
   ```bash
   docker-compose up -d
   ```

2. **Configure Airflow Connections**
   - See [Airflow Setup Guide](./runbooks/airflow-setup.md)

3. **Run Data Ingestion**
   - Enable DAGs in Airflow UI
   - Monitor execution logs

4. **Verify Data Quality**
   ```bash
   cd transform
   dbt test
   ```

---

## 📊 Data Pipeline Overview

```
API Products     ──▶  ingest_api_products DAG       ──▶  S3 (raw/products/)
PostgreSQL Orders──▶  ingest_postgres_orders DAG   ──▶  S3 (raw/orders/)
Clickstream      ──▶  ingest_clickstream_events DAG──▶  S3 (raw/events/)

                                                    ▼

                                            dbt transformation

                                                    ▼

                                        PostgreSQL Warehouse
```

---

## 🔧 Common Operations

### Start All Services
```bash
docker-compose up -d
```

### Check Service Health
```bash
docker ps
```

### View Airflow Logs
```bash
docker logs airflow-scheduler
```

### Restart Failed DAG
1. Open Airflow UI: http://localhost:8081
2. Navigate to failed DAG
3. Click "Clear" → "Confirm"

### Run dbt Models
```bash
cd transform
dbt run
```

---

## 🚨 Troubleshooting

### Airflow Won't Start
**Symptom:** Container exits immediately
**Solution:** Check PostgreSQL metadata DB is running
```bash
docker logs postgres-metadata
```

### DAG Import Errors
**Symptom:** DAG doesn't appear in UI
**Solution:** Check DAG syntax
```bash
docker exec airflow-scheduler airflow dags list
```

### Data Quality Test Failures
**Symptom:** dbt test failures
**Solution:** Check source data in S3
```bash
aws s3 ls s3://your-bucket/raw/ --recursive
```

---

## 📞 Support

For issues not covered here:
1. Check [Architecture Documentation](../architecture/)
2. Review [Data Dictionary](../data-catalog/data-dictionary.md)
3. Consult development team

---

**Last Updated:** November 10, 2025
**Maintained By:** Data Engineering Team
