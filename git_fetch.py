# git_fetch.py

import os
import subprocess
from git import Repo
from datetime import datetime

REPO_DIR = "repo"

def clone_repo(repo_url: str, local_dir: str = REPO_DIR) -> Repo:
    if os.path.exists(local_dir):
        subprocess.run(["rm", "-rf", local_dir], check=True)
    return Repo.clone_from(repo_url, local_dir)

def get_branches(repo_path: str = REPO_DIR) -> list[str]:
    repo = Repo(repo_path)
    return sorted({ref.remote_head for ref in repo.remotes.origin.refs})

def checkout_branch(branch: str, repo_path: str = REPO_DIR):
    try:
        subprocess.run(["git", "checkout", branch], cwd=repo_path, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(
            ["git", "checkout", "-t", f"origin/{branch}"],
            cwd=repo_path, check=True
        )

def get_commits(n: int = 10, repo_path: str = REPO_DIR) -> list[dict]:
    fmt = "%H%x09%an%x09%ad%x09%s"
    raw = subprocess.check_output(
        ["git", "log", f"-n{n}", "--pretty=format:" + fmt],
        cwd=repo_path
    ).decode()
    commits = []
    for line in raw.splitlines():
        h, author, date_str, msg = line.split("\t", 3)
        date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y %z")
        commits.append({
            "hash":    h,
            "author":  author,
            "date":    date.isoformat(),
            "message": msg
        })
    return commits

def list_changed_python_files(commit_hash: str, repo_path: str = REPO_DIR) -> list[str]:
    """
    Return a list of .py files changed in the given commit.
    (Added, modified, or deleted—all returned as filenames.)
    """
    raw = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
        cwd=repo_path
    ).decode().splitlines()
    return [f for f in raw if f.endswith(".py")]

def checkout_commit(commit_hash: str, repo_path: str = REPO_DIR):
    subprocess.run(["git", "checkout", commit_hash], cwd=repo_path, check=True)
