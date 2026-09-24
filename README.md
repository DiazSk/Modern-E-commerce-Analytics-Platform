# Modern E-Commerce Analytics Platform — V2 (in progress)

> This branch rebuilds the platform on **real** e-commerce events. The
> finished V1 (synthetic data on Postgres) is at tag
> [`v1-postgres-synthetic`](https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform/tree/v1-postgres-synthetic).
> Design: [`docs/superpowers/specs/2026-09-24-v2-rees46-athena-design.md`](docs/superpowers/specs/2026-09-24-v2-rees46-athena-design.md)

## Pipeline (current)

```
Kaggle REES46 (Oct 2019) ──▶ S3 raw (archive)
      │  Airflow DAG `rees46_pipeline` (manual trigger per month: a
      │  historical backfill replay, not a live feed)
      ▼
PySpark: dedupe, type, UTC ──▶ S3 processed: rees46/events/event_date=YYYY-MM-DD/
      ▼
Glue table rees46_raw.events (partition projection) ──▶ Athena
```

## Data

[REES46 "eCommerce behavior data from multi category store"](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store):
real view/cart/purchase events from one online store. Limitations: no order
IDs (the model has purchases, not orders), no event IDs (`event_key` is a
hash of all columns after exact duplicates are removed), no demographics,
2019 data from a single store.

## Run it

```bash
cp .env.example .env          # fill in AWS + Kaggle values
cd infrastructure && terraform init && terraform apply && cd ..
docker compose up -d --build  # Airflow UI: http://localhost:8081 (airflow/airflow)
```

Trigger `rees46_pipeline` with `{"month": "2019-10"}`, then in Athena
(workgroup `modern-ecommerce-analytics-platform-dev`):

```sql
select count(*) from rees46_raw.events;
```

**Resources:** Spark runs in local mode inside the Airflow container. Give
Docker at least 6 GB of memory, or lower `SPARK_DRIVER_MEMORY` in `.env`.

## Tests

```bash
pytest -q
```
