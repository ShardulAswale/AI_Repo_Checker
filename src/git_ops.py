import os
import shutil
import logging
from git import Repo

logger = logging.getLogger(__name__)

def clone_repo(repo_url: str, dest: str) -> Repo:
    """Clone (or reclone) a repo into `dest`."""
    if os.path.isdir(dest):
        logger.info(f"Removing existing directory {dest}")
        shutil.rmtree(dest)
    logger.info(f"Cloning {repo_url} → {dest}")
    return Repo.clone_from(repo_url, dest)

def get_last_commits(repo: Repo, n: int) -> list:
    """Return the last `n` commits on the active branch."""
    branch = repo.active_branch
    logger.info(f"Fetching last {n} commits on branch {branch}")
    return list(repo.iter_commits(branch, max_count=n))

def checkout_commit(repo: Repo, sha: str):
    """Checkout a commit (detached HEAD)."""
    logger.debug(f"Checkout commit {sha[:7]}")
    repo.git.checkout(sha)
