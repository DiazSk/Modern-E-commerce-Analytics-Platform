# Modern E-Commerce Analytics Platform — V2 (in progress)

> This branch rebuilds the platform on **real** e-commerce events, entirely on
> **Databricks Free Edition**. The finished V1 (synthetic data on Postgres) is at
> tag [`v1-postgres-synthetic`](https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform/tree/v1-postgres-synthetic).

## Pipeline (current)

One Databricks Workflows job, `rees46_pipeline`, defined as code in a
Databricks Asset Bundle (`databricks.yml`, `resources/rees46.yml`). It's a
historical backfill replay, triggered manually per month; not a live feed.

```
ingest     Kaggle ──▶ /Volumes/workspace/rees46/landing/2019-Oct.csv
transform  PySpark: dedupe, key, UTC ──▶ Delta workspace.rees46.raw_events
           (partitioned by event_date; the month is replaced with replaceWhere,
            and Delta rejects any row outside it)
dbt_build  dbt on the Serverless Starter Warehouse ──▶ workspace.rees46_dbt
           stg_events → int_sessions → fct_sessions (incremental) · fct_purchases
           · dim_products · dim_users · dim_date → mart_funnel_daily
           · mart_cart_abandonment
```

## Data

[REES46 "eCommerce behavior data from multi category store"](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store):
real view/cart/purchase events from one online store. Limitations: no order
IDs (the model has purchases, not orders), no event IDs (`event_key` is a
hash of all columns after exact duplicates are removed), no demographics,
2019 data from a single store.

## Run it

```bash
brew tap databricks/tap && brew install databricks
databricks auth login --host <your-workspace-url>
databricks secrets create-scope rees46
databricks secrets put-secret rees46 kaggle_username
databricks secrets put-secret rees46 kaggle_key
databricks bundle deploy
databricks bundle run rees46_pipeline --params month=2019-10
```

## Tests

Local Spark + Delta (Java 17), no Databricks account needed:

```bash
pip install pyspark==3.5.3 delta-spark==3.2.1 pytest "dbt-core==1.12.5" "dbt-spark[session]==1.11.0"
pytest -q                 # transform + job-task tests
bash ci/run_dbt_ci.sh     # dbt build + tests on a synthetic fixture (Oct, then Nov)
```

The dbt fixture in `ci/fixtures/` is synthetic (same schema as REES46);
the real dataset's license doesn't allow redistributing rows.
