# app.py

import os
import pandas as pd
from datetime import datetime
from git_fetch import (
    clone_repo,
    get_commits,
    checkout_commit,
    list_changed_python_files
)
from lint import run_pylint_on_file

REPO_DIR = "repo"

def main():
    # 1) Prompt for repo URL
    repo_url = input("Enter GitHub repo URL (HTTPS or SSH): ").strip()
    if not repo_url:
        print("No URL provided, exiting.")
        return

    # 2) Clone the repository
    print(f"Cloning {repo_url} into ./{REPO_DIR}/ …")
    clone_repo(repo_url, REPO_DIR)

    # 3) Gather commits (last 10)
    commits = get_commits(repo_path=REPO_DIR, max_count=10)
    if not commits:
        print("No commits found, exiting.")
        return

    # 4) Group by committer
    by_author = {}
    for c in commits:
        by_author.setdefault(c["author"], []).append(c)

    # 5) Build report rows
    rows = []
    for author, comms in by_author.items():
        # sort by date descending, pick newest
        comms_sorted = sorted(
            comms,
            key=lambda c: datetime.fromisoformat(c["date"]),
            reverse=True
        )
        newest = comms_sorted[0]

        last_date = newest["date"]
        num_commits = len(comms_sorted)

        # count code smells only in the newest commit, skipping tests
        checkout_commit(newest["hash"], REPO_DIR)
        changed = list_changed_python_files(newest["hash"], REPO_DIR)
        total_smells = 0
        for f in changed:
            if f.startswith("tests/") or f.startswith("test_"):
                continue
            out = run_pylint_on_file(f, REPO_DIR)
            total_smells += sum(
                1 for line in out.splitlines()
                if line and not line.startswith("Your code has been rated")
            )

        rows.append({
            "committer":        author,
            "last_commit_date": last_date,
            "number_of_commits": num_commits,
            "code_smells":      total_smells
        })

    # 6) Emit CSV
    df = pd.DataFrame(rows)
    out_path = "committer_report.csv"
    df.to_csv(out_path, index=False)
    print(f"Report generated: ./{out_path}")

if __name__ == "__main__":
    main()
