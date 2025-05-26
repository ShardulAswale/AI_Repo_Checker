# lint.py

import subprocess
import os

REPO_DIR = "repo"

def run_pylint_on_file(file_path: str, repo_path: str = REPO_DIR) -> str:
    """
    Run pylint on a single file (relative to repo_path) and return its output.
    """
    cwd = os.path.abspath(repo_path)
    try:
        output = subprocess.check_output(
            ["pylint", file_path, "--score=y", "--output-format=text"],
            cwd=cwd,
            stderr=subprocess.STDOUT
        )
        return output.decode()
    except subprocess.CalledProcessError as e:
        # non-zero exitcode still returns lint output
        return e.output.decode()
