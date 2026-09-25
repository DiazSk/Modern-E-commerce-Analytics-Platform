"""REES46 event transforms shared by the Databricks job and the tests.

transform(): dedupe exact duplicate rows, key each event, parse UTC time,
add event_date. write_month(): replace one month of the Delta table
raw_events; Delta itself rejects any row outside that month.
"""

import re
from datetime import datetime

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

MONTH_FILES = {"2019-10": "2019-Oct.csv", "2019-11": "2019-Nov.csv"}

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

# The zone ("UTC") is parsed from the text, not assumed from the session, so
# event_time is the same instant on any machine or cluster timezone.
EVENT_TIME_FORMAT = "yyyy-MM-dd HH:mm:ss z"


def read_csv(spark: SparkSession, path: str) -> DataFrame:
    """Read a REES46 CSV with the fixed schema; malformed rows fail the read."""
    return spark.read.csv(path, header=True, schema=RAW_SCHEMA, mode="FAILFAST")


def transform(df: DataFrame) -> DataFrame:
    """Drop exact duplicate rows, key each event, parse time, add event_date."""
    deduped = df.dropDuplicates()
    # to_json keeps field names and omits nulls, so rows that differ only in
    # *which* column is null still hash differently.
    keyed = deduped.withColumn(
        "event_key", F.sha2(F.to_json(F.struct(*RAW_COLUMNS)), 256)
    )
    # The source text is UTC, so its first 10 characters are the UTC date:
    # event_date never depends on the session timezone.
    dated = keyed.withColumn("event_date", F.to_date(F.substring("event_time", 1, 10)))
    parsed = dated.withColumn(
        "event_time", F.to_timestamp("event_time", EVENT_TIME_FORMAT)
    )
    return parsed.withColumn(
        "event_date", F.when(F.col("event_time").isNotNull(), F.col("event_date"))
    ).select(*OUTPUT_COLUMNS, "event_date")


def month_bounds(month: str) -> tuple[str, str]:
    """'2019-10' -> ('2019-10-01', '2019-11-01'); rejects anything else."""
    # Strict check first: the value ends up inside a SQL predicate.
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise ValueError(f"month must be YYYY-MM, got {month!r}")
    start = datetime.strptime(month, "%Y-%m")
    end = start.replace(year=start.year + start.month // 12, month=start.month % 12 + 1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def write_month(df: DataFrame, table: str, month: str) -> int:
    """Replace `month` in the Delta table `table` with `df`; return its row count.

    The write is atomic. It fails, leaving the table unchanged, if any
    event_time is unparseable or any row falls outside `month`.
    """
    start, end = month_bounds(month)
    spark = df.sparkSession
    # transform() leaves event_date null when event_time is unparseable. Fail
    # on it here, while computing the partition column, so this error fires
    # before Delta's replaceWhere check would see the null.
    checked = df.withColumn(
        "event_date",
        F.coalesce("event_date", F.raise_error(F.lit("unparseable event_time"))),
    )
    if not spark.catalog.tableExists(table):
        checked.limit(0).write.format("delta").partitionBy("event_date").saveAsTable(
            table
        )
    predicate = f"event_date >= '{start}' AND event_date < '{end}'"
    (
        checked.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", predicate)
        .saveAsTable(table)
    )
    return spark.table(table).where(predicate).count()
