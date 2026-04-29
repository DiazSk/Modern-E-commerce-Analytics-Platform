# Airflow Setup Runbook

## Purpose

Provision Airflow connections and validate the PostgreSQL ingestion DAG (`ingest_postgres_orders`) end-to-end.

## Prerequisites

- Docker services up and healthy (`docker-compose up -d`)
- Source data loaded into PostgreSQL (`scripts/load_data.py`)
- AWS S3 buckets provisioned via Terraform
- `.env` file populated with AWS credentials and Airflow Fernet key

---

## Deployment Steps

### 1. Start Airflow services

```bash
docker-compose up -d
docker ps     # confirm all containers report Healthy
```

The Airflow web UI is available at `http://localhost:8081`. Default credentials: `admin` / `admin123`.

### 2. Configure the PostgreSQL source connection

Choose one of the following methods.

**Option A — Web UI**

Navigate to **Admin → Connections → +** and submit:

| Field | Value |
|-------|-------|
| Connection Id | `postgres_source` |
| Connection Type | Postgres |
| Host | `postgres` |
| Schema | `ecommerce` |
| Login | `ecommerce_user` |
| Password | `ecommerce_pass` |
| Port | `5432` |

> **Host note:** use the Docker service name `postgres` (resolved via the `ecommerce-network` bridge), not `localhost`.

**Option B — CLI**

```bash
docker exec -it ecommerce-airflow-webserver \
    airflow connections add 'postgres_source' \
        --conn-type 'postgres' \
        --conn-host 'postgres' \
        --conn-schema 'ecommerce' \
        --conn-login 'ecommerce_user' \
        --conn-password 'ecommerce_pass' \
        --conn-port 5432
```

### 3. Configure the AWS connection

**Option A — Web UI**

Navigate to **Admin → Connections → +** and submit:

| Field | Value |
|-------|-------|
| Connection Id | `aws_default` |
| Connection Type | Amazon Web Services |
| AWS Access Key ID | *from `.env`* |
| AWS Secret Access Key | *from `.env`* |
| Region Name | `us-east-1` |

**Option B — CLI**

```bash
docker exec -it ecommerce-airflow-webserver \
    airflow connections add 'aws_default' \
        --conn-type 'aws' \
        --conn-login "$AWS_ACCESS_KEY_ID" \
        --conn-password "$AWS_SECRET_ACCESS_KEY" \
        --conn-extra '{"region_name": "us-east-1"}'
```

> **Production guidance:** use IAM roles (e.g. the `airflow_s3_role` provisioned in `infrastructure/main.tf`), not long-lived access keys.

### 4. Trigger a manual DAG run

1. Open the **DAGs** page; locate `ingest_postgres_orders`.
2. Click **Trigger DAG**, optionally setting an execution date inside the source-data window (`2023-10-29` to `2025-10-28`).
3. Confirm the DAG run starts.

### 5. Enable the schedule (optional)

Once a manual run succeeds, toggle the DAG from paused to active to enable the daily 02:00 UTC schedule.

---

## Validation

### 5.1 DAG visibility

The DAG must appear in the UI. If absent:

```bash
docker logs ecommerce-airflow-scheduler --tail 100
docker exec -it ecommerce-airflow-webserver \
    python /opt/airflow/dags/ingest_postgres_orders.py
```

### 5.2 Task-level logs (manual run)

Expected log fragments per task:

**`extract_orders`**
```
INFO - Extracting orders for date: 2025-10-28
INFO - Extracted 194 orders from PostgreSQL
INFO -    Order ID range: 4807 to 5000
INFO -    Order total sum: $25911.04
```

**`validate_data`**
```
INFO - All required fields present
INFO - No null values in critical fields
INFO - All order totals are positive
INFO - Data validation passed
```

**`load_to_s3`**
```
INFO - Uploading to S3: s3://<bucket>/raw/orders/year=2025/month=10/day=28/orders.csv
INFO - Successfully uploaded 194 orders to S3
```

### 5.3 S3 artifact verification

```bash
aws s3 ls s3://<bucket>/raw/orders/ --recursive --human-readable
aws s3 cp s3://<bucket>/raw/orders/year=2025/month=10/day=28/orders.csv - | head -n 10
```

### 5.4 Success criteria

- Airflow web UI accessible
- `postgres_source` connection passes the **Test** action
- `aws_default` connection passes the **Test** action
- `ingest_postgres_orders` is listed in the UI
- Manual DAG run completes with all five tasks in success state
- Partitioned `orders.csv` is present at the expected S3 prefix

---

## Troubleshooting

### Symptom — PostgreSQL connection refused

```
could not connect to server: Connection refused
```

**Resolution:**

1. Verify the network: `docker network inspect ecommerce-network`.
2. Verify the database is healthy: `docker logs ecommerce-postgres`.
3. Confirm host is `postgres` (not `localhost`).
4. Confirm internal port is `5432`.

### Symptom — AWS credentials missing

```
Unable to locate credentials
```

**Resolution:**

1. Validate credentials are populated in the `aws_default` connection.
2. Test outside Airflow: `aws s3 ls --profile default`.
3. Confirm IAM permissions include `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` for the target bucket. The `airflow_s3_policy` resource in `infrastructure/main.tf` provides the canonical least-privilege policy.

### Symptom — DAG not visible in UI

**Resolution:**

1. Validate Python syntax:
   ```bash
   docker exec -it ecommerce-airflow-webserver \
       python /opt/airflow/dags/ingest_postgres_orders.py
   ```
2. Inspect scheduler logs: `docker logs ecommerce-airflow-scheduler --tail 50`.
3. Wait one DAG-parsing interval (default 30 s) or restart: `docker restart ecommerce-airflow-scheduler`.

### Symptom — `No orders found for date: <YYYY-MM-DD>`

This is informational, not an error, when the execution date sits outside the source-data window. Re-trigger with a date in `2023-10-29 … 2025-10-28`. Confirm available dates with:

```sql
SELECT DATE(order_date), COUNT(*)
FROM orders
GROUP BY DATE(order_date)
ORDER BY DATE(order_date) DESC
LIMIT 10;
```

### Symptom — S3 access denied

**Resolution:**

1. Confirm the bucket name aligns across `.env`, the DAG configuration, and Airflow's AWS connection.
2. Confirm the IAM principal has the following minimum policy:

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
  "Resource": [
    "arn:aws:s3:::<bucket>",
    "arn:aws:s3:::<bucket>/*"
  ]
}
```

---

## Operations Reference

### Airflow CLI

```bash
# List configured connections
docker exec -it ecommerce-airflow-webserver airflow connections list

# Validate DAG syntax
docker exec -it ecommerce-airflow-webserver \
    python /opt/airflow/dags/ingest_postgres_orders.py

# List DAGs
docker exec -it ecommerce-airflow-webserver airflow dags list

# Trigger a manual run
docker exec -it ecommerce-airflow-webserver \
    airflow dags trigger ingest_postgres_orders

# Inspect run history
docker exec -it ecommerce-airflow-webserver \
    airflow dags list-runs -d ingest_postgres_orders

# Pull task logs for a specific execution date
docker exec -it ecommerce-airflow-webserver \
    airflow tasks logs ingest_postgres_orders extract_orders 2025-10-28
```

### Container Lifecycle

```bash
docker ps
docker restart ecommerce-airflow-scheduler
docker logs ecommerce-airflow-scheduler --tail 100 --follow
docker logs ecommerce-airflow-webserver --tail 100 --follow
docker exec -it ecommerce-airflow-webserver bash
```

### S3 Inspection

```bash
aws s3 ls
aws s3 ls s3://<bucket>/raw/orders/ --recursive --human-readable
aws s3 cp s3://<bucket>/raw/orders/year=2025/month=10/day=28/orders.csv ./
aws s3 ls s3://<bucket>/raw/orders/year=2025/month=10/day=28/ --summarize
```

---

## References

- DAG source: `dags/ingest_postgres_orders.py`
- Source schema: `scripts/init_db.sql`
- IAM least-privilege policy: `infrastructure/main.tf` (`aws_iam_policy.airflow_s3_policy`)
- Related runbook: `docs/operations/runbooks/great-expectations-reference.md`
