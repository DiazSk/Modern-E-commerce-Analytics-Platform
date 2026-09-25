import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import run_queries  # noqa: E402

SCHEMA = {"columns": [{"name": "period"}, {"name": "sessions"}]}


def response(state="SUCCEEDED", rows=None, next_link=None):
    result = {"data_array": rows or []}
    if next_link:
        result["next_chunk_internal_link"] = next_link
    return {
        "statement_id": "s1",
        "status": {"state": state, "error": {"message": "boom"}},
        "manifest": {"schema": SCHEMA},
        "result": result,
    }


def test_result_rows_collects_every_chunk():
    chunks = {
        "/c1": {"data_array": [["b", "2"]], "next_chunk_internal_link": "/c2"},
        "/c2": {"data_array": [["c", "3"]]},
    }

    header, rows = run_queries.result_rows(
        response(rows=[["a", "1"]], next_link="/c1"), chunks.__getitem__
    )

    assert header == ["period", "sessions"]
    assert rows == [["a", "1"], ["b", "2"], ["c", "3"]]


@pytest.mark.parametrize("state", ["FAILED", "CANCELED", "CLOSED"])
def test_result_rows_fails_loudly_unless_succeeded(state):
    with pytest.raises(RuntimeError, match=state):
        run_queries.result_rows(response(state=state), lambda link: {})


def test_result_rows_handles_empty_result():
    header, rows = run_queries.result_rows(
        {
            "status": {"state": "SUCCEEDED"},
            "manifest": {"schema": SCHEMA},
            "result": {},
        },
        lambda link: {},
    )
    assert header == ["period", "sessions"] and rows == []
