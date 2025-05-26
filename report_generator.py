# reporter.py

import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from git import Repo

from git_ops import checkout_commit
from lint_ops import count_lint_issues
from coverage_ops import measure_coverage

logger = logging.getLogger(__name__)

def list_python_files(repo_path: Path) -> list[str]:
    """
    Return all .py files under repo_path (relative to repo_path), recursively,
    skipping the .git directory.
    """
    return [
        str(p.relative_to(repo_path))
        for p in repo_path.rglob("*.py")
        if ".git" not in p.parts
    ]

def analyze_commits(repo: Repo, commits: list, repo_path: Path) -> list[dict]:
    """
    For each commit in `commits`:
      - checkout that commit,
      - lint all .py files (thread-pooled) to count code_smells,
      - measure coverage (per-file map) and compute an average coverage_pct,
    Returns a list of dicts, each containing:
      {
        "commit": sha,
        "author": author_name,
        "date": iso_timestamp,
        "smells": total_lint_issues,
        "cov_map": {file: pct, ...},
        "coverage_pct": average_pct
      }
    """
    results = []
    py_files = list_python_files(repo_path)

    for c in commits:
        sha    = c.hexsha
        author = c.author.name
        date   = c.committed_datetime.isoformat()

        # switch to this commit
        checkout_commit(repo, sha)

        # 1) lint in parallel
        smells = 0
        with ThreadPoolExecutor() as exe:
            futures = {
                exe.submit(count_lint_issues, f, str(repo_path)): f
                for f in py_files
            }
            for fut in as_completed(futures):
                try:
                    smells += fut.result()
                except Exception as e:
                    logger.error(f"Error linting {futures[fut]} in {sha[:7]}: {e}")
        logger.info(f"[{sha[:7]}] code_smells = {smells}")

        # 2) coverage
        try:
            cov_map = measure_coverage(str(repo_path)) or {}
        except Exception as e:
            logger.error(f"Coverage failed on {sha[:7]}: {e}")
            cov_map = {}

        # average coverage percentage for this commit
        if cov_map:
            avg_cov = sum(cov_map.values()) / len(cov_map)
        else:
            avg_cov = 0.0

        results.append({
            "commit":       sha,
            "author":       author,
            "date":         date,
            "smells":       smells,
            "cov_map":      cov_map,
            "coverage_pct": round(avg_cov, 1),
        })

    return results

def aggregate_by_committer(analyses: list) -> pd.DataFrame:
    """
    Given a list of analysis dicts from analyze_commits, group them by author,
    pick each author’s newest commit, and build a DataFrame with columns:
      committer, last_commit_hash, last_commit_date, number_of_commits,
      code_smells, coverage_pct
    """
    by_author = defaultdict(list)
    for a in analyses:
        by_author[a["author"]].append(a)

    rows = []
    for author, items in by_author.items():
        # sort descending by date to find the newest
        items.sort(key=lambda x: datetime.fromisoformat(x["date"]), reverse=True)
        newest = items[0]
        rows.append({
            "committer":          author,
            "last_commit_hash":   newest["commit"][:7],
            "last_commit_date":   newest["date"],
            "number_of_commits":  len(items),
            "code_smells":        newest["smells"],
            "coverage_pct":       newest.get("coverage_pct", 0.0),
        })

    df = pd.DataFrame(rows)
    # sort by committer name for predictability
    return df.sort_values("committer").reset_index(drop=True)
