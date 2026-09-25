from itertools import count

import pytest

from rees46_transform import (
    OUTPUT_COLUMNS,
    month_bounds,
    read_csv,
    transform,
    write_month,
)

HEADER = (
    "event_time,event_type,product_id,category_id,category_code,"
    "brand,price,user_id,user_session"
)
ROW = (
    "2019-10-01 00:00:00 UTC,view,44600062,2103807459595387724,"
    ",shiseido,35.79,541312140,72d76fde-8bb3-4e00-8c23-a032dfed738c"
)
NOV_ROW = ROW.replace("2019-10-01", "2019-11-05")
_files = count()


def load(spark, tmp_path, table, month, *rows):
    path = tmp_path / f"events_{next(_files)}.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n")
    return write_month(transform(read_csv(spark, str(path))), table, month)


def test_month_bounds_rolls_over_year():
    assert month_bounds("2019-10") == ("2019-10-01", "2019-11-01")
    assert month_bounds("2019-12") == ("2019-12-01", "2020-01-01")


@pytest.mark.parametrize("bad", ["2019-13", "2019-9", "19-10", "2019-10'; drop"])
def test_month_bounds_rejects_bad_month(bad):
    with pytest.raises(ValueError):
        month_bounds(bad)


def test_write_month_removes_exact_duplicates_but_keeps_near_duplicates(
    spark, tmp_path, table
):
    near_duplicate = ROW.replace("00:00:00", "00:00:01")

    rows = load(spark, tmp_path, table, "2019-10", ROW, ROW, near_duplicate)

    assert rows == 2
    assert spark.table(table).count() == 2


def test_write_month_creates_table_with_columns_partitioned_by_event_date(
    spark, tmp_path, table
):
    load(spark, tmp_path, table, "2019-10", ROW)

    df = spark.table(table)
    assert df.columns == OUTPUT_COLUMNS + ["event_date"]
    detail = spark.sql(f"DESCRIBE DETAIL {table}").first()
    assert detail.partitionColumns == ["event_date"]
    row = df.first()
    assert row.brand == "shiseido"
    assert row.category_code is None
    assert str(row.price) == "35.79"
    assert str(row.event_date) == "2019-10-01"


def test_write_month_stores_utc_regardless_of_session_timezone(spark, tmp_path, table):
    late = ROW.replace("2019-10-01 00:00:00", "2019-10-31 23:30:00")
    spark.conf.set("spark.sql.session.timeZone", "America/Los_Angeles")

    load(spark, tmp_path, table, "2019-10", late)

    spark.conf.set("spark.sql.session.timeZone", "UTC")
    got = spark.sql(
        f"select date_format(event_time, 'yyyy-MM-dd HH:mm:ss') as t, event_date "
        f"from {table}"
    ).first()
    assert got.t == "2019-10-31 23:30:00"
    assert str(got.event_date) == "2019-10-31"


def test_event_key_distinguishes_which_column_is_null(spark, tmp_path, table):
    brand_null = ROW.replace(",shiseido,", ",,").replace(",,,", ",beauty.skin,,")
    category_null = ROW
    both_values_same_text = ROW.replace(",shiseido,", ",beauty.skin,")

    load(
        spark,
        tmp_path,
        table,
        "2019-10",
        brand_null,
        category_null,
        both_values_same_text,
    )

    keys = [r.event_key for r in spark.table(table).collect()]
    assert len(keys) == 3
    assert len(set(keys)) == 3


def test_write_month_rejects_rows_outside_month_and_keeps_other_months(
    spark, tmp_path, table
):
    load(spark, tmp_path, table, "2019-11", NOV_ROW)
    stray = NOV_ROW.replace("2019-11-05", "2019-11-06")

    with pytest.raises(Exception, match="does not conform"):
        load(spark, tmp_path, table, "2019-10", ROW, stray)

    assert spark.table(table).count() == 1
    assert str(spark.table(table).first().event_date) == "2019-11-05"


def test_write_month_rejects_unparseable_event_time(spark, tmp_path, table):
    bad = ROW.replace("2019-10-01 00:00:00 UTC", "not-a-time")

    with pytest.raises(Exception, match="unparseable event_time"):
        load(spark, tmp_path, table, "2019-10", ROW, bad)

    assert spark.table(table).count() == 0


def test_rerunning_a_month_replaces_only_that_month(spark, tmp_path, table):
    load(spark, tmp_path, table, "2019-11", NOV_ROW)

    load(spark, tmp_path, table, "2019-10", ROW)
    rows = load(spark, tmp_path, table, "2019-10", ROW)

    assert rows == 1
    assert spark.table(table).count() == 2
