#!/usr/bin/env bash
# CI: build and test the dbt models on local Spark + Delta, in two phases:
# load October -> dbt build, then load November -> dbt build (incremental path,
# including a session that crosses midnight between the months).
set -euo pipefail

cd "$(dirname "$0")/../dbt"
export DBT_PROFILES_DIR="$PWD/../ci"
export SPARK_WAREHOUSE_DIR="${SPARK_WAREHOUSE_DIR:-$(mktemp -d)}"
rm -rf metastore_db derby.log

for month in 2019-10 2019-11; do
  python ../ci/load_fixture.py "$month"
  if [ "$month" = 2019-10 ]; then
    # Unit tests on incremental models read columns from the existing table,
    # so create schema-only relations before the first build.
    dbt run --empty --vars "{raw_schema: ci, load_month: '$month'}"
  fi
  dbt build --vars "{raw_schema: ci, load_month: '$month'}"
done
# A malformed load_month must fail at compile time, before any SQL runs.
if dbt compile --select fct_sessions --vars "{raw_schema: ci, load_month: '2019-10; drop table x'}" >/dev/null 2>&1; then
  echo "expected dbt compile to reject a malformed load_month" >&2
  exit 1
fi

echo "dbt CI build passed"
