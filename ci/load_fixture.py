"""CI only: load one synthetic REES46 month into ci.raw_events.

Goes through the real read_csv/transform/write_month path, so CI covers the
transform as well as the dbt models. Uses the same local warehouse and Hive
metastore (current directory) as the dbt-spark session in ci/profiles.yml.
"""

import os
import sys
from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rees46_transform import read_csv, transform, write_month  # noqa: E402


def main(month: str) -> None:
    builder = (
        SparkSession.builder.master("local[1]")
        .appName("load-fixture")
        .enableHiveSupport()
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.warehouse.dir", os.environ["SPARK_WAREHOUSE_DIR"])
    )
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sql("create schema if not exists ci")
    csv = ROOT / "ci" / "fixtures" / f"rees46_{month}.csv"
    rows = write_month(transform(read_csv(spark, str(csv))), "ci.raw_events", month)
    print(f"{month}: {rows} fixture rows in ci.raw_events")
    spark.stop()


if __name__ == "__main__":
    main(sys.argv[1])
