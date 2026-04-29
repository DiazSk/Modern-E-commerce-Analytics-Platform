# Development Runbook

Local-development reference for engineers working on the Modern E-Commerce Analytics Platform.

---

## Prerequisites

**Required:**

- Docker Desktop
- Git
- Python 3.11
- AWS account with S3 access (free tier sufficient)

**Recommended:**

- VS Code with Python and dbt extensions
- DBeaver or pgAdmin (external client)

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform.git
cd Modern-E-commerce-Analytics-Platform
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Populate AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AIRFLOW__CORE__FERNET_KEY
```

### 3. Start services

```bash
docker-compose up -d
```

This brings up the consolidated `postgres` container (hosting the `ecommerce`, `airflow_db`, and `metabase_db` logical databases), Redis, the Airflow components, and Metabase.

### 4. Initialise source data

```bash
python scripts/generate_data.py    # synthetic CSV generation
python scripts/load_data.py        # bulk load into PostgreSQL
```

### 5. Run the dbt project

```bash
cd transform
dbt deps
dbt build
```

### 6. Service endpoints

| Service | URL | Default credentials |
|---------|-----|---------------------|
| Airflow | `http://localhost:8081` | `admin` / `admin123` |
| Metabase | `http://localhost:3001` | Set at first login |

---

## Project Structure

```
Modern-E-commerce-Analytics-Platform/
├── dags/                       # Airflow DAG definitions
│   ├── ingest_api_products.py
│   ├── ingest_postgres_orders.py
│   └── ingest_clickstream_events.py
├── transform/                  # dbt project
│   ├── models/
│   │   ├── staging/            # cleaning + standardisation
│   │   └── marts/              # business logic
│   ├── tests/
│   └── dbt_project.yml
├── scripts/                    # utility scripts
│   ├── generate_data.py        # synthetic data generation
│   ├── load_data.py            # bulk PostgreSQL load
│   ├── init_db.sql             # source-DB schema bootstrap
│   ├── init_multi_db.sh        # multi-DB bootstrap for the consolidated postgres container
│   └── setup_airflow_connections.py
├── infrastructure/             # Terraform IaC
├── docs/                       # documentation
├── docker-compose.yml          # service orchestration
└── requirements.txt            # Python dependencies
```

---

## Local Testing

### dbt

```bash
cd transform

# Run all tests
dbt test

# Test a specific model
dbt test --select dim_customers

# Persist test failures to the warehouse
dbt test --store-failures
```

### Great Expectations

```bash
python scripts/run_checkpoint.py
open gx/uncommitted/data_docs/local_site/index.html
```

### Python unit tests

```bash
pytest tests/
pytest --cov=scripts tests/
```

### DAG-syntax validation

```bash
python dags/ingest_postgres_orders.py
python dags/ingest_clickstream_events.py
python dags/data_quality_checks.py
```

---

## Development Workflow

### 1. Feature branch

```bash
git checkout -b feature/<concise-description>
# edit files
dbt run  --select <model>
dbt test --select <model>
git commit -m "feat: <imperative summary>"
git push origin feature/<concise-description>
```

### 2. Code review

- Open a pull request.
- Confirm CI checks pass.
- Address reviewer feedback before merge.

### 3. Merge

```bash
# After PR approval
git checkout develop
git pull origin develop
```

---

## Coding Standards

### Python

- Follow PEP 8.
- Use type hints.
- Add docstrings to public functions.
- Maximum line length: 100 characters.

### SQL

- Lowercase keywords.
- `snake_case` identifiers.
- CTEs for complex logic.
- Comments explain *why*, not *what*.

### dbt

- One model per file.
- Models live in `staging/` or `marts/` subdirectories.
- Every model has at least `unique`, `not_null`, and applicable `relationships` tests.
- Document each model in `schema.yml`.

---

## Debugging

### Airflow DAG issues

```bash
docker logs ecommerce-airflow-scheduler
docker exec ecommerce-airflow-scheduler airflow dags list

# Validate DAG syntax (catches import errors)
python dags/<dag_file>.py
```

### dbt model issues

```bash
dbt compile --select <model>          # inspect target/compiled/
dbt run --select <model> --debug      # verbose execution
```

### Database connectivity

```bash
docker exec ecommerce-postgres \
    psql -U ecommerce_user -d ecommerce -c "SELECT 1;"
```

---

## Related Documentation

- Synthetic data generation: [data-generation.md](./data-generation.md)
- Airflow service runbook: [../operations/runbooks/airflow-setup.md](../operations/runbooks/airflow-setup.md)
- Great Expectations runbook: [../operations/runbooks/great-expectations-reference.md](../operations/runbooks/great-expectations-reference.md)
- Metabase operations: [../analytics/metabase/metabase-operations-runbook.md](../analytics/metabase/metabase-operations-runbook.md)

---

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make changes with tests.
4. Submit a pull request.
5. Address review feedback.
