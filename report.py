# report.py

import pandas as pd
from datetime import datetime
from git_fetch import (
    clone_repo,
    get_commits,
    checkout_commit,
    list_changed_python_files
)
from lint import run_pylint_on_file

def generate_committer_report(
    repo_url: str,
    local_dir: str = "repo",
    max_commits: int = 10
) -> pd.DataFrame:
    """
    For the last `max_commits` commits:
      - Group by author
      - For each author:
          * last_commit_hash    = short SHA of their newest commit
          * last_commit_message = commit message of that commit
          * last_commit_date    = ISO date of that commit
          * number_of_commits   = count within that window
          * code_smells         = lint issues on that newest commit only
    """
    # 1) Clone fresh
    clone_repo(repo_url, local_dir)

    # 2) Fetch commits
    commits = get_commits(repo_path=local_dir, max_count=max_commits)
    if not commits:
        return pd.DataFrame(columns=[
            "committer",
            "last_commit_hash",
            "last_commit_message",
            "last_commit_date",
            "number_of_commits",
            "code_smells"
        ])

    # 3) Parse dates and group by author
    for c in commits:
        c["_dt"] = datetime.fromisoformat(c["date"])
    by_author: dict[str, list[dict]] = {}
    for c in commits:
        by_author.setdefault(c["author"], []).append(c)

    rows = []
    for author, comms in by_author.items():
        # sort by date descending → pick newest
        comms_sorted = sorted(comms, key=lambda c: c["_dt"], reverse=True)
        newest = comms_sorted[0]

        # metrics
        last_hash    = newest["hash"][:7]
        last_msg     = newest["message"]
        last_date    = newest["_dt"].isoformat()
        commit_count = len(comms_sorted)

        # lint only that newest commit
        checkout_commit(newest["hash"], local_dir)
        files_changed = list_changed_python_files(newest["hash"], local_dir)
        smells = 0
        for f in files_changed:
            if f.startswith("tests/") or f.startswith("test_"):
                continue
            out = run_pylint_on_file(f, local_dir)
            smells += sum(
                1 for line in out.splitlines()
                if line and not line.startswith("Your code has been rated")
            )

        rows.append({
            "committer":            author,
            "last_commit_hash":     last_hash,
            "last_commit_message":  last_msg,
            "last_commit_date":     last_date,
            "number_of_commits":    commit_count,
            "code_smells":          smells
        })

    df = pd.DataFrame(rows)
    return df.sort_values("committer").reset_index(drop=True)
