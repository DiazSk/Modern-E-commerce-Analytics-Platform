"""Build docs/index.html (GitHub Pages) from the committed analysis CSVs.

The page template lives in analysis/site/template.html. This script fills its
%%TOKENS%% with numbers formatted from analysis/results/*.csv and embeds every
result and extract CSV as JSON for the in-page explorer. Only aggregates are
read; nothing here touches Databricks.
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read_dir(folder: Path) -> dict[str, list[dict]]:
    return {
        p.stem: list(csv.DictReader(p.open(newline="")))
        for p in sorted(folder.glob("*.csv"))
    }


def pct(x: str, digits: int = 1) -> str:
    return f"{100 * float(x):.{digits}f}%"


def pp(x: str, digits: int = 1) -> str:
    v = 100 * float(x)
    return f"{'−' if v < 0 else '+'}{abs(v):.{digits}f}"


def millions(x: str, digits: int = 1) -> str:
    return f"{int(x) / 1e6:.{digits}f}M"


def tokens(results: dict[str, list[dict]]) -> dict[str, str]:
    totals = results["q0_totals"][0]
    profile = results["q0_data_profile"][0]
    overall = {r["metric"]: r for r in results["q1_overall_black_friday"]}
    aband = results["q2_abandonment_black_friday"][0]
    naive = {
        r["metric"]: r
        for r in results["q3_anomaly_impact"]
        if r["baseline"].startswith("naive")
    }
    daily = {r["event_date"]: r for r in results["q0_anomaly_daily"]}
    cart, buy = overall["cart_rate"], overall["purchase_rate"]
    return {
        "EVENTS": millions(totals["events"]),
        "SESSIONS": millions(totals["sessions"]),
        "PURCHASES": millions(totals["purchases"], 2),
        "USERS": millions(totals["users"]),
        "CART_BASE": pct(cart["baseline"]),
        "CART_BF": pct(cart["black_friday"]),
        "CART_DIFF": pp(cart["diff"]),
        "CART_LOW": pp(cart["ci_low"]),
        "CART_HIGH": pp(cart["ci_high"]),
        "BUY_BASE": pct(buy["baseline"], 2),
        "BUY_BF": pct(buy["black_friday"], 2),
        "BUY_DIFF": pp(buy["diff"], 2),
        "BUY_LOW": pp(buy["ci_low"], 2),
        "BUY_HIGH": pp(buy["ci_high"], 2),
        "ABANDON_BASE": pct(aband["baseline_rate"]),
        "ABANDON_BF": pct(aband["black_friday_rate"]),
        "ABANDON_DIFF": pp(aband["diff"]),
        "NAIVE_CART_DIFF": pp(naive["cart_rate"]["diff"]),
        "NAIVE_ABANDON_DIFF": pp(naive["cart_abandonment"]["diff"]),
        "NAIVE_BUY_DIFF": pp(naive["purchase_rate"]["diff"], 2),
        "GAP_CARTS": f"{int(daily['2019-11-15']['carts']):,}",
        "GAP_PURCHASES_17": f"{int(daily['2019-11-17']['purchases']):,}",
        "SPAN_DAY": pct(profile["share_spanning_days"], 2),
        "SPAN_MAX": profile["max_span_days"],
        "MEDIAN_SECONDS": profile["median_seconds"],
    }


def build(results_dir: Path, extracts_dir: Path) -> str:
    results = read_dir(results_dir)
    # The weekly mart extract feeds Tableau only; the page uses the daily grain.
    extracts = {
        k: v for k, v in read_dir(extracts_dir).items() if k != "mart_cart_abandonment"
    }
    html = (HERE / "site" / "template.html").read_text()
    for key, value in tokens(results).items():
        html = html.replace(f"%%{key}%%", value)
    # JSON inside <script>: escape '<' so data can never close the tag.
    data = json.dumps({"results": results, "extracts": extracts}, separators=(",", ":"))
    html = html.replace("%%DATA%%", data.replace("<", "\\u003c"))
    leftover = sorted(set(part.split("%%")[0] for part in html.split("%%")[1::2]))
    if leftover:
        raise ValueError(f"unfilled template tokens: {leftover}")
    return html


def main() -> None:
    out = ROOT / "docs" / "index.html"
    out.write_text(build(HERE / "results", HERE / "extracts"))
    print(f"{out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
