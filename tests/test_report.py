import pandas as pd
import pytest
import report

@pytest.fixture(autouse=True)
def fake_git_and_lint(monkeypatch):
    # Stub clone_repo so it does nothing
    monkeypatch.setattr(report, "clone_repo", lambda url, d: None)

    # Provide a mix of commits for two authors
    fake_commits = [
        # Alice: two commits
        {"hash": "h1", "author": "Alice", "date": "2025-01-01T00:00:00+00:00", "message": "foo"},
        {"hash": "h2", "author": "Alice", "date": "2025-01-02T00:00:00+00:00", "message": "bar"},
        # Bob: one commit
        {"hash": "h3", "author": "Bob",   "date": "2025-01-03T00:00:00+00:00", "message": "baz"},
    ]
    monkeypatch.setattr(report, "get_commits", lambda **kw: fake_commits)

    # Track current commit in report module
    def track_checkout(h, d):
        report.current_commit = h
    monkeypatch.setattr(report, "checkout_commit", track_checkout)

    # Each commit changes a unique file
    def fake_list(hash_, d):
        return {"h1": ["a.py"], "h2": ["b.py"], "h3": ["c.py"]}[hash_]
    monkeypatch.setattr(report, "list_changed_python_files", fake_list)

    # Lint issues: only b.py (Alice's newest) has 2 issues; c.py (Bob) has 3
    def fake_lint(f, d):
        if report.current_commit == "h2":
            return "E\nE\n"
        if report.current_commit == "h3":
            return "E\nE\nE\n"
        return ""
    monkeypatch.setattr(report, "run_pylint_on_file", fake_lint)

def test_generate_committer_report():
    df = report.generate_committer_report("url", local_dir="repo", max_commits=3)
    # Should have two rows: Alice and Bob
    assert set(df["committer"]) == {"Alice", "Bob"}

    alice = df[df["committer"] == "Alice"].iloc[0]
    # Alice made 2 commits, code_smells from newest only (h2 -> 2 issues)
    assert alice["number_of_commits"] == 2
    assert alice["code_smells"] == 2

    bob = df[df["committer"] == "Bob"].iloc[0]
    # Bob made 1 commit, code_smells from that commit (h3 -> 3 issues)
    assert bob["number_of_commits"] == 1
    assert bob["code_smells"] == 3
