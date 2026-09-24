"""Convert one month of REES46 events CSV into partitioned Parquet.

Output: <output_dir>/event_date=YYYY-MM-DD/*.parquet with the columns of the
Glue table rees46_raw.events (infrastructure/athena.tf). The month is
validated after writing; on any problem the output directory is removed so
nothing half-valid can be uploaded.
"""

import argparse
import os
import shutil

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

RAW_SCHEMA = StructType(
    [
        StructField("event_time", StringType()),
        StructField("event_type", StringType()),
        StructField("product_id", LongType()),
        StructField("category_id", LongType()),
        StructField("category_code", StringType()),
        StructField("brand", StringType()),
        StructField("price", DecimalType(10, 2)),
        StructField("user_id", LongType()),
        StructField("user_session", StringType()),
    ]
)
RAW_COLUMNS = [f.name for f in RAW_SCHEMA.fields]
OUTPUT_COLUMNS = ["event_key"] + RAW_COLUMNS

EVENT_TIME_FORMAT = "yyyy-MM-dd HH:mm:ss 'UTC'"


def get_spark() -> SparkSession:
    return (
        SparkSession.builder.master("local[*]")
        .appName("rees46-events-to-parquet")
        .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "4g"))
        .getOrCreate()
    )


def transform(df: DataFrame) -> DataFrame:
    """Drop exact duplicate rows, key each event, parse time, add event_date."""
    deduped = df.dropDuplicates()
    # to_json keeps field names and omits nulls, so rows that differ only in
    # *which* column is null still hash differently.
    keyed = deduped.withColumn(
        "event_key", F.sha2(F.to_json(F.struct(*RAW_COLUMNS)), 256)
    )
    parsed = keyed.withColumn(
        "event_time", F.to_timestamp("event_time", EVENT_TIME_FORMAT)
    )
    return parsed.withColumn(
        "event_date", F.date_format("event_time", "yyyy-MM-dd")
    ).select(*OUTPUT_COLUMNS, "event_date")


def run(
    input_csv: str, output_dir: str, month: str, spark: SparkSession | None = None
) -> int:
    spark = spark or get_spark()
    # The source timestamps are UTC; store them as UTC instants whatever the
    # machine's timezone is.
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    raw = spark.read.csv(input_csv, header=True, schema=RAW_SCHEMA, mode="FAILFAST")
    (
        transform(raw)
        .repartition("event_date")
        .write.mode("overwrite")
        .partitionBy("event_date")
        .parquet(output_dir)
    )

    written = spark.read.parquet(output_dir)
    stats = written.agg(
        F.count("*").alias("rows"),
        F.sum(F.col("event_time").isNull().cast("int")).alias("unparseable"),
        F.sum((F.date_format("event_date", "yyyy-MM") != month).cast("int")).alias(
            "outside"
        ),
    ).first()
    problems = []
    if stats.unparseable:
        problems.append(f"{stats.unparseable} rows with unparseable event_time")
    if stats.outside:
        problems.append(f"{stats.outside} rows outside {month}")
    if problems:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise ValueError(f"{input_csv}: " + "; ".join(problems))
    return stats.rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv")
    parser.add_argument("output_dir")
    parser.add_argument("month", help="YYYY-MM the file must contain")
    args = parser.parse_args()
    print(run(args.input_csv, args.output_dir, args.month))


if __name__ == "__main__":
    main()
