# Great Expectations - Quick Reference Card

## 🚀 Common Commands

### Initialization
```bash
# First time setup
python scripts/init_great_expectations.py

# Create expectation suite
python scripts/create_expectations.py
```

### Running Validations
```bash
# Run checkpoint manually
great_expectations checkpoint run orders_checkpoint

# Test via Airflow
airflow tasks test data_quality_validation validate_data_quality 2025-11-03

# Trigger Airflow DAG
airflow dags trigger data_quality_validation
```

### Viewing Results
```bash
# Open data docs
start great_expectations\uncommitted\data_docs\local_site\index.html

# Check Airflow logs
airflow tasks logs data_quality_validation validate_data_quality <date>
```

---

## 📋 Expectations Reference

| Expectation Type | Purpose | Example |
|------------------|---------|---------|
| `expect_table_row_count_to_be_between` | Table size | 1K-10M rows |
| `expect_column_values_to_be_unique` | Uniqueness | Primary keys |
| `expect_column_values_to_not_be_null` | Completeness | Foreign keys |
| `expect_column_values_to_be_between` | Range checks | quantity 1-100 |
| `expect_column_values_to_be_in_set` | Valid values | order_status |

---

## 🔧 Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| orders_quality_suite.yml | Validation rules | expectations/ |
| orders_checkpoint.yml | Checkpoint config | checkpoints/ |
| data_quality_checks.py | Airflow DAG | dags/ |

---

## 🆘 Troubleshooting

| Issue | Command | Fix |
|-------|---------|-----|
| "Module not found" | `pip install great-expectations==0.18.8` | Install GE |
| "Cannot connect" | `docker ps` | Check PostgreSQL |
| "Checkpoint not found" | `python scripts/init_great_expectations.py` | Re-initialize |
| "Validation failed" | View data docs | Check failed expectations |

---

## 📊 File Structure

```
great_expectations/
├── expectations/          # Your validation rules
├── checkpoints/           # How to run validations
├── uncommitted/          # Results (gitignored)
│   ├── data_docs/       # Web UI
│   └── validations/     # Result files
└── .gitignore
```

---

## 🎯 Validation Flow

```
1. fact_orders loaded (dbt run)
       ↓
2. GE checkpoint runs (orders_checkpoint)
       ↓
3. 15 expectations evaluated
       ↓
4. Results logged + docs updated
       ↓
5a. All pass ✓ → Proceed
5b. Some fail ✗ → Alert + Block
```

---

## 🎓 Key Concepts

**Expectation**: A single validation rule (e.g., "quantity must be positive")

**Suite**: Collection of expectations for a table (e.g., orders_quality_suite)

**Checkpoint**: Configuration for running a suite (e.g., orders_checkpoint)

**Validation**: Act of running expectations against data

**Data Docs**: Auto-generated web UI showing validation results

---

## 📝 Adding New Expectations

```python
# In scripts/create_expectations.py

# Add your expectation
validator.expect_column_values_to_match_regex(
    column="email",
    regex=r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$',
    meta={
        "notes": "Email format validation",
        "business_rule": "Must be valid email address"
    }
)

# Save and re-run
validator.save_expectation_suite()
```

Then:
```bash
python scripts/create_expectations.py
great_expectations checkpoint run orders_checkpoint
```

---

## 🎯 Production Checklist

- [ ] GE initialized
- [ ] Expectations created (15+)
- [ ] Checkpoint runs successfully
- [ ] Airflow DAG tested
- [ ] Email alerts configured
- [ ] Data docs accessible
- [ ] Scheduled daily

---

**Quick Start**: `python scripts/init_great_expectations.py`
**Run Validation**: `great_expectations checkpoint run orders_checkpoint`
**View Results**: Data docs at `uncommitted/data_docs/local_site/index.html`
