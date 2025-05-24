# lint.py

import subprocess

REPO_DIR = "repo"

def run_pylint_on_file(file_path: str, repo_path: str = REPO_DIR) -> str:
    """
    Run pylint on a single file within the repo directory and
    return its full report.
    """
    try:
        # Note: we run in cwd=repo_path and pass the relative path.
        output = subprocess.check_output(
            ["pylint", file_path, "--score=y", "--output-format=text"],
            cwd=repo_path,
            stderr=subprocess.STDOUT
        ).decode()
        return output
    except subprocess.CalledProcessError as e:
        # Pylint returns non-zero exit codes on lint errors, so return its output
        return e.output.decode()
