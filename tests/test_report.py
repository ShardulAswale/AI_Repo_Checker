# tests/test_report.py

import pandas as pd
import pytest
import report

@pytest.fixture(autouse=True)
def patch_git_and_lint(monkeypatch):
    # stub clone_repo
    monkeypatch.setattr(report, "clone_repo", lambda url, d: None)
    # fake commits
    fake = [
        {"hash": "h1", "author": "Alice", "date": "2025-01-01T00:00:00+00:00", "message": "msg1"},
        {"hash": "h2", "author": "Alice", "date": "2025-01-02T00:00:00+00:00", "message": "msg2"},
        {"hash": "h3", "author": "Bob",   "date": "2025-01-03T00:00:00+00:00", "message": "msg3"},
    ]
    monkeypatch.setattr(report, "get_commits", lambda **kw: fake)
    # checkout no-op
    monkeypatch.setattr(report, "checkout_commit", lambda h, d: None)
    # pretend each commit changes one file
    def fake_list(hash_, d):
        return ["foo.py"] if hash_ != "h3" else ["bar.py"]
    monkeypatch.setattr(report, "list_changed_python_files", fake_list)
    # fake lint: h1->1 issue, h2->2 issues, h3->3 issues
    def fake_lint(f, d):
        if f == "foo.py" and report.current_commit == "h1":
            return "E\n"
        if f == "foo.py" and report.current_commit == "h2":
            return "E\nE\n"
        if f == "bar.py":
            return "E\nE\nE\n"
        return ""
    # Track current commit
    def set_current(hash_, d):
        report.current_commit = hash_
    monkeypatch.setattr(report, "checkout_commit", set_current)
    monkeypatch.setattr(report, "run_pylint_on_file", fake_lint)

def test_generate_committer_report(monkeypatch):
    # generate with max_commits=3
    df = report.generate_committer_report("url", local_dir="repo", max_commits=3)
    assert isinstance(df, pd.DataFrame)
    # Two committers: Alice and Bob
    assert set(df["committer"]) == {"Alice", "Bob"}
    # Alice: two commits, code_smells from newest commit (h2) => 2
    row_a = df[df["committer"] == "Alice"].iloc[0]
    assert row_a["number_of_commits"] == 2
    assert row_a["code_smells"] == 2
    # Bob: one commit => 3
    row_b = df[df["committer"] == "Bob"].iloc[0]
    assert row_b["number_of_commits"] == 1
    assert row_b["code_smells"] == 3
