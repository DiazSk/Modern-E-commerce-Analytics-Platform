import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import build_site  # noqa: E402

RESULTS = {
    "q0_totals": "events,sessions,purchases,users,first_day,last_day\n"
    "109820004,23016650,1659703,5316649,2019-10-01,2019-11-30\n",
    "q0_data_profile": "sessions,share_spanning_days,share_spanning_week,"
    "max_span_days,median_seconds\n23016650,0.00282,0.00035,60,61\n",
    "q1_overall_black_friday": "metric,black_friday,baseline,diff,ci_low,ci_high,"
    "black_friday_sessions,baseline_sessions\n"
    "cart_rate,0.1171,0.0921,0.0250,0.0246,0.0255,2390542,9199507\n"
    "purchase_rate,0.0560,0.0525,0.0036,0.0032,0.0039,2390542,9199507\n",
    "q2_abandonment_black_friday": "black_friday_rate,baseline_rate,diff,ci_low,"
    "ci_high,black_friday_items,baseline_items\n"
    "0.543362,0.538844,0.0045,0.0025,0.0066,318147,795126\n",
    "q3_anomaly_impact": "metric,baseline,black_friday,baseline_rate,diff,ci_low,"
    "ci_high,black_friday_n,baseline_n\n"
    "cart_abandonment,naive_includes_nov14_17,0.5434,0.6668,-0.1234,-0.1253,-0.1216,1,1\n"
    "cart_rate,naive_includes_nov14_17,0.1171,0.1343,-0.0172,-0.0176,-0.0167,1,1\n"
    "purchase_rate,naive_includes_nov14_17,0.0560,0.0568,-0.0008,-0.0011,-0.0004,1,1\n",
    "q0_anomaly_daily": "event_date,events,views,carts,purchases\n"
    "2019-11-15,6205340,5737078,468262,0\n2019-11-17,6379921,5783122,411604,185195\n",
}
EXTRACTS = {
    "mart_funnel_daily": "session_date,category_l1,sessions,carted_sessions,"
    "purchased_sessions,cart_rate,purchase_rate,is_black_friday_week\n"
    "2019-11-29,</script><b>x,10,2,1,0.2,0.1,true\n",
    "abandonment_daily": "category_l1,price_band,cart_date,carted_items,abandoned_items\n"
    "electronics,4,2019-11-29,10,4\n",
}


def write(tmp_path):
    for folder, files in (("results", RESULTS), ("extracts", EXTRACTS)):
        (tmp_path / folder).mkdir()
        for name, text in files.items():
            (tmp_path / folder / f"{name}.csv").write_text(text)
    return tmp_path / "results", tmp_path / "extracts"


def test_build_renders_corrected_headline_and_naive_reversal(tmp_path):
    html = build_site.build(*write(tmp_path))

    assert "9.2%" in html and "11.7%" in html and "+2.5 pp" in html  # cart reach
    assert "−12.3 pp" in html and "−1.7 pp" in html  # what the gap did
    assert "468,262" in html and "185,195" in html
    assert "109.8M" in html and "23.0M" in html and "1.66M" in html


def test_build_embeds_all_csv_rows_as_json(tmp_path):
    html = build_site.build(*write(tmp_path))

    raw = re.search(
        r'<script id="data" type="application/json">(.*?)</script>', html, re.S
    ).group(1)
    data = json.loads(raw)
    assert data["extracts"]["mart_funnel_daily"][0]["category_l1"] == "</script><b>x"
    assert data["results"]["q0_totals"][0]["events"] == "109820004"


def test_build_escapes_script_breakouts_and_leaves_no_tokens(tmp_path):
    html = build_site.build(*write(tmp_path))

    assert "</script><b>x" not in html
    assert "%%" not in html
