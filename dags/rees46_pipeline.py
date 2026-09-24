"""REES46 events: Kaggle -> S3 raw archive -> Spark -> S3 partitioned Parquet.

A historical backfill replay, not a live feed: trigger manually once per
month of the 2019 dataset. Re-running a month replaces its partitions.
"""

import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task
from airflow.models.param import Param

DATASET = "mkechinov/ecommerce-behavior-data-from-multi-category-store"
FILES = {"2019-10": "2019-Oct.csv", "2019-11": "2019-Nov.csv"}
DATA_DIR = Path(os.environ.get("REES46_DATA_DIR", "/opt/airflow/data/rees46"))
ARCHIVE_PREFIX = "rees46/archive/"
EVENTS_PREFIX = "rees46/events/"


def locate_csv(data_dir: Path, filename: str) -> Path:
    """Return the extracted CSV, unzipping Kaggle's .zip download if needed."""
    csv = data_dir / filename
    archive = data_dir / f"{filename}.zip"
    if not csv.exists():
        if not archive.exists():
            raise FileNotFoundError(f"neither {csv} nor {archive} exists")
        with zipfile.ZipFile(archive) as z:
            z.extract(filename, data_dir)
    return csv


def partition_uploads(local_dir: Path) -> dict[str, list[Path]]:
    """Map each local event_date=... partition to its S3 prefix and files."""
    return {
        f"{EVENTS_PREFIX}{part.name}/": sorted(part.glob("*.parquet"))
        for part in sorted(local_dir.glob("event_date=*"))
        if part.is_dir()
    }


@dag(
    dag_id="rees46_pipeline",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={"month": Param("2019-10", enum=list(FILES))},
    tags=["rees46"],
    doc_md=__doc__,
)
def rees46_pipeline():
    @task
    def fetch(**context) -> str:
        import boto3

        filename = FILES[context["params"]["month"]]
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        archive = DATA_DIR / f"{filename}.zip"
        if not (DATA_DIR / filename).exists() and not archive.exists():
            subprocess.run(
                [
                    "kaggle",
                    "datasets",
                    "download",
                    "-d",
                    DATASET,
                    "-f",
                    filename,
                    "-p",
                    str(DATA_DIR),
                ],
                check=True,
            )
        csv = locate_csv(DATA_DIR, filename)

        # Keep what the source delivered in the raw zone.
        source = archive if archive.exists() else csv
        s3 = boto3.client("s3")
        bucket = os.environ["REES46_RAW_BUCKET"]
        key = ARCHIVE_PREFIX + source.name
        if "Contents" not in s3.list_objects_v2(Bucket=bucket, Prefix=key):
            s3.upload_file(str(source), bucket, key)
        return str(csv)

    @task
    def to_parquet(csv_path: str, **context) -> str:
        from spark.events_to_parquet import run

        month = context["params"]["month"]
        out = DATA_DIR / "parquet" / month
        rows = run(csv_path, str(out), month)
        print(f"{month}: wrote {rows} rows to {out}")
        return str(out)

    @task
    def upload(local_dir: str) -> int:
        import boto3

        s3 = boto3.client("s3")
        bucket = os.environ["REES46_PROCESSED_BUCKET"]
        uploaded = 0
        # ponytail: delete-then-upload leaves a partition briefly empty while
        # it is replaced; fine for a manually triggered replay, use a staging
        # prefix + swap if anything reads the table during loads.
        for prefix, files in partition_uploads(Path(local_dir)).items():
            pages = s3.get_paginator("list_objects_v2").paginate(
                Bucket=bucket, Prefix=prefix
            )
            for page in pages:
                old = [{"Key": o["Key"]} for o in page.get("Contents", [])]
                if old:
                    s3.delete_objects(Bucket=bucket, Delete={"Objects": old})
            for f in files:
                s3.upload_file(str(f), bucket, prefix + f.name)
                uploaded += 1
        return uploaded

    upload(to_parquet(fetch()))


rees46_pipeline()
