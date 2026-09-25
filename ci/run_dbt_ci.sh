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
  dbt build --vars "{raw_schema: ci, load_month: '$month'}"
done
# (Task 3 adds the malformed-load_month check here.)

echo "dbt CI build passed"
