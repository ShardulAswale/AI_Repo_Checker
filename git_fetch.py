# git_fetch.py

import os
import shutil
from git import Repo
from datetime import datetime

REPO_DIR = "repo"

def clone_repo(repo_url: str, local_dir: str = REPO_DIR) -> Repo:
    """
    Clone (or re-clone) the GitHub repo into local_dir.
    """
    if os.path.isdir(local_dir):
        shutil.rmtree(local_dir)
    return Repo.clone_from(repo_url, local_dir)

def get_branches(repo_path: str = REPO_DIR) -> list[str]:
    """
    Return a list of remote branch names (e.g. ['main','dev',...]).
    """
    repo = Repo(repo_path)
    repo.remotes.origin.fetch()
    return sorted({ref.remote_head for ref in repo.remotes.origin.refs})

def checkout_branch(branch: str, repo_path: str = REPO_DIR):
    """
    Checkout a branch by name, creating a local tracking branch if needed.
    """
    repo = Repo(repo_path)
    git = repo.git
    try:
        git.checkout(branch)
    except Exception:
        git.checkout("-t", f"origin/{branch}")

def get_commits(repo_path: str = REPO_DIR, max_count: int = 10) -> list[dict]:
    """
    Return the last `max_count` commits on the current branch, newest first.
    Each dict contains: hash, author, date (ISO), message.
    """
    repo = Repo(repo_path)
    commits = list(repo.iter_commits(repo.active_branch, max_count=max_count))
    result = []
    for c in commits:
        result.append({
            "hash":    c.hexsha,
            "author":  c.author.name,
            "date":    c.committed_datetime.isoformat(),
            "message": c.message.strip()
        })
    return result

def checkout_commit(commit_hash: str, repo_path: str = REPO_DIR):
    """
    Checkout the given commit (detached HEAD).
    """
    repo = Repo(repo_path)
    repo.git.checkout(commit_hash)

def list_changed_python_files(commit_hash: str, repo_path: str = REPO_DIR) -> list[str]:
    """
    List all .py files changed in the given commit.
    """
    repo = Repo(repo_path)
    raw = repo.git.diff_tree(
        "--no-commit-id", "--name-only", "-r", commit_hash
    )
    return [f for f in raw.splitlines() if f.endswith(".py")]
