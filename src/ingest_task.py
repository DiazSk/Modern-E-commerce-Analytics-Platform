"""Databricks job task 1: download one month of REES46 into the landing volume.

A historical backfill replay: the job is triggered manually per month.
Skips the download if the CSV or its Kaggle .zip is already in the volume.
"""

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

# Sibling import. Databricks' serverless runner exec()s this file without
# __file__; sys.argv[0] is then the script path.
_here = os.path.dirname(os.path.abspath(globals().get("__file__", sys.argv[0])))
sys.path.insert(0, _here)

from rees46_transform import MONTH_FILES  # noqa: E402

DATASET = "mkechinov/ecommerce-behavior-data-from-multi-category-store"
SECRET_SCOPE = "rees46"


def locate_csv(data_dir: Path, filename: str) -> Path:
    """Return the extracted CSV, unzipping Kaggle's .zip download if needed."""
    csv = data_dir / filename
    archive = data_dir / f"{filename}.zip"
    if csv.exists():
        return csv
    if not archive.exists():
        raise FileNotFoundError(f"neither {csv} nor {archive} exists")
    try:
        with zipfile.ZipFile(archive) as z:
            z.extract(filename, data_dir)
    except zipfile.BadZipFile as e:
        archive.unlink()
        raise RuntimeError(
            f"{archive} was incomplete and has been removed; re-run to download again"
        ) from e
    return csv


def kaggle_env() -> dict[str, str]:
    """Kaggle CLI credentials from the Databricks secret scope."""
    from databricks.sdk.runtime import dbutils

    return {
        **os.environ,
        "KAGGLE_USERNAME": dbutils.secrets.get(SECRET_SCOPE, "kaggle_username"),
        "KAGGLE_KEY": dbutils.secrets.get(SECRET_SCOPE, "kaggle_key"),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True, choices=sorted(MONTH_FILES))
    parser.add_argument("--volume-dir", required=True)
    args = parser.parse_args(argv)

    data_dir = Path(args.volume_dir)
    filename = MONTH_FILES[args.month]
    if (
        not (data_dir / filename).exists()
        and not (data_dir / f"{filename}.zip").exists()
    ):
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
                str(data_dir),
            ],
            check=True,
            env=kaggle_env(),
        )
    csv = locate_csv(data_dir, filename)
    print(f"{args.month}: {csv} ({csv.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
