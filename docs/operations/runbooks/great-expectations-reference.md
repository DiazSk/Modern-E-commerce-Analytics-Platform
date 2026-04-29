# Great Expectations Runbook

## Purpose

Operate the Great Expectations data-quality validation suite that runs against the `fact_orders` table after each dbt build. This document covers initialisation, on-demand validation, scheduled validation via Airflow, and the troubleshooting matrix.

## Prerequisites

- Python 3.11 environment with `great-expectations==0.18.8` installed
- PostgreSQL source database reachable from the validation host
- `gx/` directory present at the repository root with the `orders_quality_suite` and `orders_checkpoint` artefacts
- For scheduled runs: Airflow `data_quality_validation` DAG visible in the UI

---

## Deployment Steps

### 1. Initialise the Great Expectations context (first-time only)

```bash
python scripts/init_great_expectations.py
python scripts/create_expectations.py
```

### 2. Execute the checkpoint on demand

```bash
great_expectations checkpoint run orders_checkpoint
```

### 3. Execute the checkpoint via Airflow

```bash
# Single-task test against an arbitrary execution date
airflow tasks test data_quality_validation validate_data_quality 2025-11-03

# Manually trigger the full DAG
airflow dags trigger data_quality_validation
```

---

## Validation

### 4.1 Inspect data docs

```bash
# Linux/macOS
open gx/uncommitted/data_docs/local_site/index.html

# Windows
start gx\uncommitted\data_docs\local_site\index.html
```

### 4.2 Inspect Airflow logs

```bash
airflow tasks logs data_quality_validation validate_data_quality <execution_date>
```

### 4.3 Success criteria

- Checkpoint exits with `success: True`
- Data docs render the latest validation as **passing** for all expectations
- Airflow DAG `data_quality_validation` lands in the success state

---

## Expectation Reference

Expectations applied to `fact_orders`:

| Expectation Type | Purpose | Example |
|------------------|---------|---------|
| `expect_table_row_count_to_be_between` | Table size | 1K–10M rows |
| `expect_column_values_to_be_unique` | Uniqueness | Primary keys |
| `expect_column_values_to_not_be_null` | Completeness | Foreign keys |
| `expect_column_values_to_be_between` | Numeric range | `quantity` 1–100 |
| `expect_column_values_to_be_in_set` | Categorical values | `order_status` |

---

## Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `orders_quality_suite.yml` | Validation rules | `gx/expectations/` |
| `orders_checkpoint.yml` | Checkpoint config | `gx/checkpoints/` |
| `data_quality_checks.py` | Airflow DAG | `dags/` |

---

## Repository Layout

```
gx/
├── expectations/           # validation rules
├── checkpoints/            # checkpoint configurations
├── uncommitted/            # results (gitignored)
│   ├── data_docs/          # static HTML report site
│   └── validations/        # raw result files
└── .gitignore
```

---

## Validation Flow

```
1. fact_orders is materialised by dbt
       ↓
2. Airflow triggers orders_checkpoint
       ↓
3. Configured expectations are evaluated
       ↓
4. Results are persisted; data docs are regenerated
       ↓
5a. All pass  → downstream tasks proceed
5b. Any fail  → DAG fails, alert is dispatched
```

---

## Domain Glossary

| Term | Definition |
|------|------------|
| Expectation | A single validation rule (e.g. "`quantity` must be > 0"). |
| Suite | A named collection of expectations bound to a table. |
| Checkpoint | A configuration that runs a suite against a data source. |
| Validation | The act of running expectations against a snapshot of data. |
| Data Docs | The auto-generated HTML site that reports validation results. |

---

## Adding a New Expectation

```python
# scripts/create_expectations.py

validator.expect_column_values_to_match_regex(
    column="email",
    regex=r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$",
    meta={
        "notes": "Email format validation",
        "business_rule": "Must be a valid email address",
    },
)

validator.save_expectation_suite()
```

Apply and re-run:

```bash
python scripts/create_expectations.py
great_expectations checkpoint run orders_checkpoint
```

---

## Troubleshooting

| Symptom | Diagnostic | Resolution |
|---------|------------|------------|
| `ModuleNotFoundError: great_expectations` | `pip show great-expectations` | `pip install great-expectations==0.18.8` |
| `Cannot connect to data source` | `docker ps` | Confirm the `postgres` container is healthy |
| `Checkpoint not found` | `ls gx/checkpoints/` | Re-run `python scripts/init_great_expectations.py` |
| Validation failed | Inspect data docs | Identify failing expectation; remediate the data or adjust the suite |

---

## Production Readiness Checklist

- [ ] Great Expectations context initialised (`gx/` populated)
- [ ] Expectation suite contains the agreed minimum (15+) of rules
- [ ] Checkpoint runs cleanly on demand
- [ ] Airflow DAG `data_quality_validation` is paused but tested
- [ ] Email alerts are configured for DAG failure
- [ ] Data docs are accessible to data consumers
- [ ] DAG schedule is enabled (daily)

---

## References

- Airflow DAG: `dags/data_quality_checks.py`
- Source schema: `scripts/init_db.sql`
- dbt fact model: `transform/models/marts/core/fact_orders.sql`
