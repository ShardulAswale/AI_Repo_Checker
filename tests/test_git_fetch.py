# tests/test_git_fetch.py

import os
import tempfile
import subprocess
import pytest
from git import Repo
import git_fetch

@pytest.fixture
def tmp_repo(tmp_path):
    # Initialize a bare repo with two commits
    origin = tmp_path / "origin"
    origin.mkdir()
    repo = Repo.init(origin)
    # Commit1
    f1 = origin / "a.py"
    f1.write_text("print('hello')\n")
    repo.index.add([str(f1.name)])
    repo.index.commit("init commit")
    # Commit2: change a.py
    f1.write_text("print('world')\n")
    repo.index.add([str(f1.name)])
    repo.index.commit("second commit")
    return origin

def test_clone_and_get_commits(tmp_repo, tmp_path):
    clone_dir = tmp_path / "clone"
    # Clone from local path via file://
    cloned = git_fetch.clone_repo(f"file://{tmp_repo}", str(clone_dir))
    assert (clone_dir / "a.py").exists()
    # Fetch commits (default max_count=10)
    commits = git_fetch.get_commits(repo_path=str(clone_dir))
    assert isinstance(commits, list)
    assert len(commits) == 2
    hashes = [c["hash"] for c in commits]
    # Latest commit first
    assert commits[0]["message"] == "second commit"
    # Test checkout and listing
    first_hash = commits[-1]["hash"]
    git_fetch.checkout_commit(first_hash, str(clone_dir))
    changed = git_fetch.list_changed_python_files(first_hash, str(clone_dir))
    assert "a.py" in changed

def test_get_branches(tmp_repo, tmp_path):
    # create a branch and test get_branches
    repo = Repo(str(tmp_repo))
    repo.git.checkout("-b", "dev")
    branches = git_fetch.get_branches(repo_path=str(tmp_repo))
    assert "dev" in branches
