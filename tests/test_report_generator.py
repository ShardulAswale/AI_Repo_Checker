import pytest
from pathlib import Path
from src.report_generator import list_python_files, aggregate_by_committer

def test_list_python_files(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.py").write_text("y=2")
    # hidden .git folder should be skipped
    (tmp_path / ".git").mkdir()
    files = list_python_files(tmp_path)
    assert set(files) == {"a.py", "sub/b.py"}

def test_aggregate_by_committer():
    analyses = [
       {"commit":"aaa", "author":"Alice","date":"2025-01-02T00:00:00","smells":1,"coverage_pct":50.0},
       {"commit":"bbb", "author":"Bob","date":"2025-01-03T00:00:00","smells":2,"coverage_pct":60.0},
       {"commit":"ccc", "author":"Alice","date":"2025-01-04T00:00:00","smells":3,"coverage_pct":70.0},
    ]
    df = aggregate_by_committer(analyses)
    # Columns and ordering
    assert list(df.columns) == [
        "committer",
        "last_commit_hash",
        "last_commit_date",
        "number_of_commits",
        "code_smells",
        "coverage_pct"
    ]
    # Alice should have 2 commits, pick the newest
    alice = df[df["committer"]=="Alice"].iloc[0]
    assert alice["number_of_commits"] == 2
    assert alice["last_commit_hash"] == "ccc"
    assert pytest.approx(alice["coverage_pct"]) == 70.0
    assert alice["code_smells"] == 3
