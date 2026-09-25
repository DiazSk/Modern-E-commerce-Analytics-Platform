# From V1 to V2

## V1 (tag `v1-postgres-synthetic`)
Airflow → S3 → Postgres → dbt → Metabase on **synthetic** Faker data (5,000
orders). A self-audit found claims the code didn't back up: CI had been red since
April 2026, an SCD2 dimension was joined on current rows only, the benchmark
numbers had never been measured, and there were partition settings Postgres
ignores. The V1 fixes (green CI, real SCD2 via a dbt snapshot, removal of the
unverified claims) were merged before V1 was tagged.

## Why V2
Synthetic data can't produce findings. V2 rebuilds the same idea on **109.8M
real events** and adds an analysis layer that answers two business questions
with confidence intervals.

## What changed
| | V1 | V2 |
|---|---|---|
| Data | Faker, 5,000 orders | REES46, 109.8M events (Oct–Nov 2019) |
| Platform | Airflow + AWS S3 + Postgres | Databricks Free Edition (Workflows, Unity Catalog, Delta) |
| Transform | Python loaders | PySpark with a month-scoped `replaceWhere` guard |
| Models | dbt on Postgres | dbt on Databricks SQL; incremental sessions |
| CI | dbt on a seeded Postgres | dbt on local Spark + Delta with a synthetic fixture |
| Output | Metabase dashboards | Memo with effect sizes and CIs, GitHub Pages dashboard |

## What real data surfaced
Two issues that synthetic data could never have produced:
- **Session IDs span weeks.** A dbt test comparing the incremental `fct_sessions`
  with a from-scratch aggregation found 2,951 stale sessions. The model now
  recomputes every session with events in the loaded month.
- **A tracking gap on Nov 14–17.** On Nov 15 the store logged 468,262 carts and no
  purchases, and left in the baseline, those four days reversed all three headline Black Friday
  findings. The analysis excludes them, and the dashboard lets you put them back in.

## Platform history
The first V2 design targeted AWS (S3 + Athena), then Azure (ADLS + Azure SQL).
Both free-tier accounts expired or ran out of credit. V2 runs on Databricks Free
Edition so it costs nothing and doesn't expire, and CI needs no cloud account at
all.
