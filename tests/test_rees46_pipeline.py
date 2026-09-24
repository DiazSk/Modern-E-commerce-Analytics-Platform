import zipfile
from pathlib import Path

import pytest
from airflow.models import DagBag

from dags.rees46_pipeline import locate_csv, partition_uploads


def test_dags_import_without_errors():
    bag = DagBag(dag_folder="dags", include_examples=False)
    assert bag.import_errors == {}
    dag = bag.dags["rees46_pipeline"]
    assert [t.task_id for t in dag.topological_sort()] == [
        "fetch",
        "to_parquet",
        "upload",
    ]


def test_locate_csv_unzips_kaggle_archive(tmp_path):
    with zipfile.ZipFile(tmp_path / "2019-Oct.csv.zip", "w") as z:
        z.writestr("2019-Oct.csv", "a,b\n1,2\n")

    path = locate_csv(tmp_path, "2019-Oct.csv")

    assert path == tmp_path / "2019-Oct.csv"
    assert path.read_text() == "a,b\n1,2\n"


def test_locate_csv_reuses_existing_csv(tmp_path):
    (tmp_path / "2019-Oct.csv").write_text("already here\n")

    assert locate_csv(tmp_path, "2019-Oct.csv").read_text() == "already here\n"


def test_locate_csv_fails_clearly_when_nothing_downloaded(tmp_path):
    with pytest.raises(FileNotFoundError, match="2019-Oct.csv"):
        locate_csv(tmp_path, "2019-Oct.csv")


def test_partition_uploads_maps_only_parquet_in_partition_dirs(tmp_path):
    part = tmp_path / "event_date=2019-10-01"
    part.mkdir()
    (part / "part-0000.snappy.parquet").write_bytes(b"x")
    (part / ".part-0000.snappy.parquet.crc").write_bytes(b"x")
    (tmp_path / "_SUCCESS").write_bytes(b"")

    uploads = partition_uploads(tmp_path)

    assert uploads == {
        "rees46/events/event_date=2019-10-01/": [part / "part-0000.snappy.parquet"]
    }
