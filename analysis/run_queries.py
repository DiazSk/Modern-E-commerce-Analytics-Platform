"""Run the analysis SQL on the Databricks SQL warehouse and save CSVs.

Uses the Databricks CLI's existing login (`databricks auth login`); prints
no credentials. Every file in analysis/queries/ becomes
analysis/results/<name>.csv, and the two marts are exported to
analysis/extracts/ for Tableau Public. Only aggregates are written.
"""

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
WAREHOUSE_NAME = "Serverless Starter Warehouse"
EXTRACTS = {
    "mart_funnel_daily": "select * from workspace.rees46_dbt.mart_funnel_daily "
    "order by session_date, category_l1",
    # Session grain (mart_funnel_daily is session x category), for the
    # dashboard's all-categories funnel so it matches q1_overall exactly.
    "sessions_daily": "select session_date, count(*) as sessions, "
    "sum(cast(reached_cart as int)) as carted_sessions, "
    "sum(cast(reached_purchase as int)) as purchased_sessions "
    "from workspace.rees46_dbt.fct_sessions group by session_date order by session_date",
    "mart_cart_abandonment": "select * from workspace.rees46_dbt.mart_cart_abandonment "
    "order by week_start, category_l1, price_band",
    # Daily grain for the dashboard, so its Nov 14-17 toggle is exact to the day.
    "abandonment_daily": """
        with sp as (
            select user_session, product_id,
                   min(case when event_type = 'cart' then event_date end) as cart_date,
                   max(case when event_type = 'purchase' then 1 else 0 end) as purchased
            from workspace.rees46_dbt.stg_events
            where user_session is not null
            group by user_session, product_id
        )
        select p.category_l1, p.price_band, sp.cart_date,
               count(*) as carted_items, sum(1 - sp.purchased) as abandoned_items
        from sp join workspace.rees46_dbt.dim_products p on sp.product_id = p.product_id
        where sp.cart_date is not null
        group by p.category_l1, p.price_band, sp.cart_date
        order by sp.cart_date, p.category_l1, p.price_band""",
}


def cli(*args: str, body: dict | None = None) -> dict:
    cmd = ["databricks", *args, "--output", "json"]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    return json.loads(
        subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    )


def warehouse_id() -> str:
    for w in cli("warehouses", "list"):
        if w["name"] == WAREHOUSE_NAME:
            return w["id"]
    raise RuntimeError(f"warehouse {WAREHOUSE_NAME!r} not found")


def result_rows(
    response: dict, fetch_chunk: Callable[[str], dict]
) -> tuple[list[str], list[list[str]]]:
    """Header and all rows of a finished statement, following every chunk."""
    state = response["status"]["state"]
    if state != "SUCCEEDED":
        message = response["status"].get("error", {}).get("message", "")
        raise RuntimeError(f"statement {state}: {message}")
    header = [c["name"] for c in response["manifest"]["schema"]["columns"]]
    chunk = response.get("result") or {}
    rows = list(chunk.get("data_array") or [])
    while chunk.get("next_chunk_internal_link"):
        chunk = fetch_chunk(chunk["next_chunk_internal_link"])
        rows += chunk.get("data_array") or []
    return header, rows


def run(statement: str, wh: str) -> tuple[list[str], list[list[str]]]:
    body = {"warehouse_id": wh, "statement": statement, "wait_timeout": "50s"}
    response = cli("api", "post", "/api/2.0/sql/statements", body=body)
    while response["status"]["state"] in ("PENDING", "RUNNING"):
        time.sleep(5)
        response = cli(
            "api", "get", f"/api/2.0/sql/statements/{response['statement_id']}"
        )
    return result_rows(response, lambda link: cli("api", "get", link))


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"{path.relative_to(HERE.parent)}: {len(rows)} rows")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="run a single query or extract by name")
    args = parser.parse_args(argv)
    wh = warehouse_id()
    jobs = {
        p.stem: (p.read_text(), HERE / "results" / f"{p.stem}.csv")
        for p in sorted((HERE / "queries").glob("*.sql"))
    }
    jobs |= {
        name: (sql, HERE / "extracts" / f"{name}.csv") for name, sql in EXTRACTS.items()
    }
    for name, (sql, out) in jobs.items():
        if args.only in (None, name):
            write_csv(out, *run(sql, wh))


if __name__ == "__main__":
    main()
