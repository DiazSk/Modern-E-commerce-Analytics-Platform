"""Databricks job task 2: landing CSV for one month -> Delta raw_events.

Replaces that month in the table (atomic; rows outside the month fail the
write), then deletes the landing files: the Delta table is the durable copy.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling import

from pyspark.sql import SparkSession  # noqa: E402

from rees46_transform import (  # noqa: E402
    MONTH_FILES,
    read_csv,
    transform,
    write_month,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True, choices=sorted(MONTH_FILES))
    parser.add_argument("--volume-dir", required=True)
    parser.add_argument("--table", required=True)
    args = parser.parse_args(argv)

    spark = SparkSession.builder.getOrCreate()
    csv = Path(args.volume_dir) / MONTH_FILES[args.month]
    rows = write_month(transform(read_csv(spark, str(csv))), args.table, args.month)
    print(f"{args.month}: {rows} rows in {args.table}")

    for landing in (csv, csv.with_name(csv.name + ".zip")):
        landing.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
