# lint_ops.py

import os
import logging
from flake8.api import legacy as flake8

logger = logging.getLogger(__name__)

def count_lint_issues(file_rel: str, repo_path: str) -> int:
    """
    Run Flake8 on a single file (in-process) and return the number of lint
    errors/warnings. Safe to call from multiple threads.
    """
    abs_path = os.path.join(repo_path, file_rel)
    logger.debug(f"Linting {file_rel} via Flake8")

    # Configure flake8 to only select the error/warning codes you care about.
    style = flake8.get_style_guide(
        ignore=[],
        select=["E", "W", "F", "C"]   # errors, warnings, pyflakes and cyclomatic
    )

    report = style.check_files([abs_path])
    count = report.total_errors
    logger.debug(f"Found {count} lint issues in {file_rel}")
    return count
