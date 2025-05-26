# main.py

import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from git_ops import clone_repo, get_last_commits
from report_generator import analyze_commits, aggregate_by_committer
from lint_ops import count_lint_issues
from coverage_ops import measure_coverage
from git import Repo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def compute_total_lints(repo_path: Path) -> int:
    py_files = [
        str(p.relative_to(repo_path))
        for p in repo_path.rglob("*.py")
        if ".git" not in p.parts
    ]
    total = 0
    with ThreadPoolExecutor() as exe:
        futures = {
            exe.submit(count_lint_issues, f, str(repo_path)): f
            for f in py_files
        }
        for fut in as_completed(futures):
            try:
                total += fut.result()
            except Exception as e:
                logger.error(f"Error linting {futures[fut]}: {e}")
    return total

def main():
    parser = argparse.ArgumentParser(
        description="GitHub Commit & Committer Evaluation Tool"
    )
    parser.add_argument("repo_url", help="GitHub repo URL")
    parser.add_argument("-n", "--num-commits", type=int, default=10)
    parser.add_argument("-o", "--output-prefix", default="report")
    args = parser.parse_args()

    workdir = Path("repo")
    repo = clone_repo(args.repo_url, str(workdir))

    # List all .py files fetched
    all_py = [
        str(p.relative_to(workdir))
        for p in workdir.rglob("*.py")
        if ".git" not in p.parts
    ]
    logger.info(f"Found {len(all_py)} Python files:")
    for f in sorted(all_py):
        logger.info(f"  – {f}")

    # Total lints at HEAD
    total_lints = compute_total_lints(workdir)
    logger.info(f"Total lint issues in repository: {total_lints}")

    # Overall coverage at HEAD
    cov_map = measure_coverage(str(workdir)) or {}
    overall_cov = (
        sum(cov_map.values()) / len(cov_map)
        if cov_map else 0.0
    )
    logger.info(f"Overall coverage: {overall_cov:.1f}%")

    # Per‐commit analysis
    commits  = get_last_commits(repo, args.num_commits)
    analyses = analyze_commits(repo, commits, workdir)

    # Commit‐level report
    commit_rows = []
    for a in analyses:
        cov_map = a.get("cov_map", {})
        avg_cov = (
            sum(cov_map.values()) / len(cov_map)
            if cov_map else 0.0
        )
        commit_rows.append({
            "commit":       a["commit"][:7],
            "author":       a["author"],
            "date":         a["date"],
            "code_smells":  a["smells"],
            "coverage_pct": round(avg_cov, 1),
        })
      # … earlier code …

    # Commit-level report
    df_commits = pd.DataFrame(commit_rows)
    commit_csv = f"{args.output_prefix}_commit_metrics.csv"
    df_commits.to_csv(commit_csv, index=False)
    logger.info(f"Wrote commit-level metrics → {commit_csv}")

    # Contributor-level report
    df_contrib = aggregate_by_committer(analyses)
    contrib_csv = f"{args.output_prefix}_contributor_metrics.csv"
    df_contrib.to_csv(contrib_csv, index=False)
    logger.info(f"Wrote contributor-level metrics → {contrib_csv}")

if __name__ == "__main__":
    main()
