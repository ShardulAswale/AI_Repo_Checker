# tests/test_app.py

import os
import sys
import pandas as pd
import pytest

# make sure the repo root is on sys.path so we can import app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app

@pytest.fixture(autouse=True)
def fake_environment(monkeypatch, tmp_path):
    # Redirect REPO_DIR to a tmp dir
    repo_dir = tmp_path / "repo"
    monkeypatch.setattr(app, "REPO_DIR", str(repo_dir))

    # Stub out clone_repo so it just creates the directory
    def fake_clone(url, d):
        os.makedirs(d, exist_ok=True)
    monkeypatch.setattr(app, "clone_repo", fake_clone)

    # Fake commits: two commits by Alice, one by Bob
    fake_commits = [
        {"hash": "h1", "author": "Alice", "date": "2025-01-01T00:00:00+00:00", "message": "init"},
        {"hash": "h2", "author": "Alice", "date": "2025-01-02T00:00:00+00:00", "message": "update"},
        {"hash": "h3", "author": "Bob",   "date": "2025-01-03T00:00:00+00:00", "message": "add feature"},
    ]
    monkeypatch.setattr(app, "get_commits", lambda **kw: fake_commits)

    # No-op for checkout_commit
    monkeypatch.setattr(app, "checkout_commit", lambda *args, **kwargs: None)

    # Fake changed files: each commit touches one file
    def fake_list_files(commit_hash, repo_path):
        return ["foo.py"] if commit_hash in ("h1", "h2") else ["bar.py"]
    monkeypatch.setattr(app, "list_changed_python_files", fake_list_files)

    # Fake lint counts: commit h1→1 issue, h2→2 issues, h3→3 issues
    def fake_lint(file_path, repo_path):
        if app.current_commit == "h1":
            return "E\n"
        if app.current_commit == "h2":
            return "E\nE\n"
        if app.current_commit == "h3":
            return "E\nE\nE\n"
        return ""
    # Track which commit is checked out
    def track_checkout(commit_hash, repo_path):
        app.current_commit = commit_hash
    monkeypatch.setattr(app, "checkout_commit", track_checkout)
    monkeypatch.setattr(app, "run_pylint_on_file", fake_lint)

    yield

def test_main_generates_report(tmp_path, monkeypatch, capsys):
    # Simulate user input for repo URL
    monkeypatch.setattr("builtins.input", lambda prompt="": "https://dummy/repo.git")

    # Change working dir to tmp_path so output CSV lands here
    monkeypatch.chdir(tmp_path)

    # Run the main function
    app.main()

    # Capture stdout
    out = capsys.readouterr().out
    assert "Cloning https://dummy/repo.git" in out
    assert "Report generated:" in out

    # Verify CSV exists
    csv_path = tmp_path / "committer_report.csv"
    assert csv_path.exists()

    # Read and validate CSV contents
    df = pd.read_csv(csv_path)
    # Should have two authors
    authors = set(df["committer"])
    assert authors == {"Alice", "Bob"}

    # Alice: newest commit h2 → lint issues = 2
    alice = df[df["committer"] == "Alice"].iloc[0]
    assert alice["number_of_commits"] == 2
    assert alice["code_smells"] == 2

    # Bob: only commit h3 → lint issues = 3
    bob = df[df["committer"] == "Bob"].iloc[0]
    assert bob["number_of_commits"] == 1
    assert bob["code_smells"] == 3
