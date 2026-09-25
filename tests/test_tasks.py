import sys
import zipfile
from pathlib import Path

import pytest

import ingest_task
import transform_task
from tests.test_transform import HEADER, ROW


def test_locate_csv_unzips_kaggle_archive(tmp_path):
    with zipfile.ZipFile(tmp_path / "2019-Oct.csv.zip", "w") as z:
        z.writestr("2019-Oct.csv", "a,b\n1,2\n")

    path = ingest_task.locate_csv(tmp_path, "2019-Oct.csv")

    assert path == tmp_path / "2019-Oct.csv"
    assert path.read_text() == "a,b\n1,2\n"


def test_locate_csv_reuses_existing_csv(tmp_path):
    (tmp_path / "2019-Oct.csv").write_text("already here\n")

    assert ingest_task.locate_csv(tmp_path, "2019-Oct.csv").read_text() == (
        "already here\n"
    )


def test_locate_csv_fails_clearly_when_nothing_downloaded(tmp_path):
    with pytest.raises(FileNotFoundError, match="2019-Oct.csv"):
        ingest_task.locate_csv(tmp_path, "2019-Oct.csv")


def test_locate_csv_removes_corrupt_zip(tmp_path):
    archive = tmp_path / "2019-Oct.csv.zip"
    archive.write_bytes(b"PK\x03\x04 truncated download")

    with pytest.raises(RuntimeError, match="re-run to download again"):
        ingest_task.locate_csv(tmp_path, "2019-Oct.csv")

    assert not archive.exists()


def test_transform_task_loads_month_and_removes_landing_files(spark, tmp_path, table):
    (tmp_path / "2019-Oct.csv").write_text(f"{HEADER}\n{ROW}\n")
    (tmp_path / "2019-Oct.csv.zip").write_bytes(b"archive")

    transform_task.main(
        ["--month", "2019-10", "--volume-dir", str(tmp_path), "--table", table]
    )

    assert spark.table(table).count() == 1
    assert not (tmp_path / "2019-Oct.csv").exists()
    assert not (tmp_path / "2019-Oct.csv.zip").exists()


def test_transform_task_rejects_unknown_month(tmp_path, table):
    with pytest.raises(SystemExit):
        transform_task.main(
            ["--month", "2019-9", "--volume-dir", str(tmp_path), "--table", table]
        )


@pytest.mark.parametrize("script", ["ingest_task.py", "transform_task.py"])
def test_task_scripts_import_siblings_when_run_without___file__(script, monkeypatch):
    # Databricks' serverless runner exec()s the task file without __file__
    # (sys.argv[0] is the script path), so the sibling import must not need it.
    path = Path(__file__).resolve().parents[1] / "src" / script
    monkeypatch.setattr(sys, "argv", [str(path)])
    monkeypatch.setattr(sys, "path", [p for p in sys.path if not p.endswith("/src")])
    monkeypatch.delitem(sys.modules, "rees46_transform", raising=False)

    exec(compile(path.read_text(), str(path), "exec"), {"__name__": "task"})
