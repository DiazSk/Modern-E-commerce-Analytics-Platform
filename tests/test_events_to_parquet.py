from pathlib import Path

import pytest

from spark.events_to_parquet import OUTPUT_COLUMNS, run

HEADER = (
    "event_time,event_type,product_id,category_id,category_code,"
    "brand,price,user_id,user_session"
)
ROW = (
    "2019-10-01 00:00:00 UTC,view,44600062,2103807459595387724,"
    ",shiseido,35.79,541312140,72d76fde-8bb3-4e00-8c23-a032dfed738c"
)


def write_csv(tmp_path: Path, *rows: str) -> str:
    path = tmp_path / "events.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n")
    return str(path)


def read_output(spark, out: str):
    return spark.read.parquet(out)


def test_run_removes_exact_duplicates_but_keeps_near_duplicates(spark, tmp_path):
    near_duplicate = ROW.replace("00:00:00", "00:00:01")
    csv = write_csv(tmp_path, ROW, ROW, near_duplicate)
    out = str(tmp_path / "out")

    rows = run(csv, out, "2019-10", spark)

    assert rows == 2
    assert read_output(spark, out).count() == 2


def test_run_writes_glue_columns_partitioned_by_event_date(spark, tmp_path):
    csv = write_csv(tmp_path, ROW)
    out = str(tmp_path / "out")

    run(csv, out, "2019-10", spark)

    assert (Path(out) / "event_date=2019-10-01").is_dir()
    df = read_output(spark, out)
    assert df.columns == OUTPUT_COLUMNS + ["event_date"]
    row = df.first()
    assert row.brand == "shiseido"
    assert row.category_code is None
    assert str(row.price) == "35.79"


def test_run_stores_utc_regardless_of_session_timezone(spark, tmp_path):
    late = ROW.replace("2019-10-01 00:00:00", "2019-10-31 23:30:00")
    csv = write_csv(tmp_path, late)
    out = str(tmp_path / "out")
    spark.conf.set("spark.sql.session.timeZone", "America/Los_Angeles")

    run(csv, out, "2019-10", spark)

    spark.conf.set("spark.sql.session.timeZone", "UTC")
    got = (
        read_output(spark, out)
        .selectExpr("date_format(event_time, 'yyyy-MM-dd HH:mm:ss') as t", "event_date")
        .first()
    )
    assert got.t == "2019-10-31 23:30:00"
    assert str(got.event_date) == "2019-10-31"


def test_event_key_distinguishes_which_column_is_null(spark, tmp_path):
    brand_null = ROW.replace(",shiseido,", ",,").replace(
        ",,,", ",beauty.skin,,"
    )  # category_code set, brand null
    category_null = ROW  # category_code null, brand set
    both_values_same_text = ROW.replace(",shiseido,", ",beauty.skin,")
    csv = write_csv(tmp_path, brand_null, category_null, both_values_same_text)
    out = str(tmp_path / "out")

    run(csv, out, "2019-10", spark)

    keys = [r.event_key for r in read_output(spark, out).collect()]
    assert len(keys) == 3
    assert len(set(keys)) == 3


def test_run_rejects_rows_outside_month(spark, tmp_path):
    november = ROW.replace("2019-10-01", "2019-11-01")
    csv = write_csv(tmp_path, ROW, november)
    out = tmp_path / "out"

    with pytest.raises(ValueError, match="outside 2019-10"):
        run(csv, str(out), "2019-10", spark)

    assert not out.exists()


def test_run_rejects_unparseable_event_time(spark, tmp_path):
    bad = ROW.replace("2019-10-01 00:00:00 UTC", "not-a-time")
    csv = write_csv(tmp_path, ROW, bad)
    out = tmp_path / "out"

    with pytest.raises(ValueError, match="unparseable event_time"):
        run(csv, str(out), "2019-10", spark)

    assert not out.exists()


def test_rerunning_a_month_replaces_output(spark, tmp_path):
    csv = write_csv(tmp_path, ROW)
    out = str(tmp_path / "out")

    run(csv, out, "2019-10", spark)
    run(csv, out, "2019-10", spark)

    assert read_output(spark, out).count() == 1
