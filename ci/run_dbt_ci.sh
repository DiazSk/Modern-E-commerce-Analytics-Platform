#!/usr/bin/env bash
# CI: build and test the dbt models on local Spark + Delta, in two phases:
# load October -> dbt build, then load November -> dbt build (incremental path,
# including a session that crosses midnight between the months).
set -euo pipefail

cd "$(dirname "$0")/../dbt"
export DBT_PROFILES_DIR="$PWD/../ci"
if [ -z "${SPARK_WAREHOUSE_DIR:-}" ]; then
  SPARK_WAREHOUSE_DIR="$(mktemp -d)"
  created_warehouse=1
fi
export SPARK_WAREHOUSE_DIR
cleanup() {
  rm -rf metastore_db derby.log
  if [ "${created_warehouse:-0}" = 1 ]; then rm -rf "$SPARK_WAREHOUSE_DIR"; fi
}
trap cleanup EXIT
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
# A malformed load_month must fail at compile time with the explicit message.
for bad in '2019-10; drop table x' '2019-9' $'2019-10\n'; do
  if out=$(dbt compile --select fct_sessions --vars "{raw_schema: ci, load_month: \"${bad//$'\n'/\\n}\"}" 2>&1); then
    echo "expected dbt compile to reject load_month=$(printf %q "$bad")" >&2
    exit 1
  fi
  grep -q "load_month must be YYYY-MM" <<<"$out" || { echo "wrong failure for $(printf %q "$bad"):" >&2; tail -5 <<<"$out" >&2; exit 1; }
done

echo "dbt CI build passed"
