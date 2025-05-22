# repo_analyzer.py

import os
import subprocess

REPO_PATH = "repo"

def clone_repo(repo_url, target_dir=REPO_PATH):
    if os.path.exists(target_dir):
        subprocess.run(["rm", "-rf", target_dir], check=True)
    subprocess.run(["git", "clone", repo_url, target_dir], check=True)

def get_commits(n=10, repo_path=REPO_PATH):
    """
    Return list of dicts: { hash, author, date }
    """
    fmt = "%H%x09%an%x09%ad"  # hash, author, date (tab-separated)
    raw = subprocess.check_output(
        ["git", "log", f"-n{n}", "--pretty=format:" + fmt],
        cwd=repo_path
    ).decode()
    commits = []
    for line in raw.splitlines():
        h, author, date = line.split("\t")
        commits.append({"hash": h, "author": author, "date": date})
    return commits

def checkout_commit(commit_hash, repo_path=REPO_PATH):
    subprocess.run(["git", "checkout", commit_hash], cwd=repo_path, check=True)

def list_python_files(repo_path=REPO_PATH):
    py_files = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, f), repo_path)
                py_files.append(rel)
    return py_files

def run_linters_on_file(file, repo_path=REPO_PATH):
    path = os.path.join(repo_path, file)
    try:
        out = subprocess.check_output(["flake8", path], stderr=subprocess.STDOUT).decode()
        return out or "No issues found ✔️"
    except subprocess.CalledProcessError as e:
        return e.output.decode()
