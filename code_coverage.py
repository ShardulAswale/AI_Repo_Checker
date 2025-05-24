# code_coverage.py

import subprocess
import re

REPO_DIR = "repo"
_RANGE_RE = re.compile(r"^(\d+)(?:-(\d+))?$")

def run_code_coverage(repo_path: str = REPO_DIR) -> str:
    """
    Run pytest under coverage (omitting tests) and return the full report.
    """
    omit = "--omit=*/test_*.py"
    try:
        subprocess.run(
            ["coverage", "run", omit, "--source=.", "-m", "pytest", "-q"],
            cwd=repo_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        report = subprocess.check_output(
            ["coverage", "report", "--show-missing", omit],
            cwd=repo_path
        ).decode()
        return report
    except subprocess.CalledProcessError as e:
        err = e.output.decode() if getattr(e, "output", None) else str(e)
        return f"[Coverage Error]\n{err}"

def parse_coverage(report: str):
    """
    Parse coverage report into:
      cov_map: {filename: coverage_percent}
      miss_map: {filename: [missing_line_numbers]}
    """
    cov_map = {}
    miss_map = {}
    for line in report.splitlines():
        parts = line.strip().split()
        if len(parts) >= 5 and parts[0] not in ("Name", "TOTAL"):
            fname, _, _, cov_perc, missing = parts[:5]
            # Parse percentage
            try:
                cov_map[fname] = float(cov_perc.strip("%"))
            except ValueError:
                cov_map[fname] = 0.0
            # Parse missing line numbers
            if missing == "-":
                miss_map[fname] = []
            else:
                nums = []
                for seg in missing.split(","):
                    m = _RANGE_RE.match(seg)
                    if not m:
                        continue
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else start
                    nums.extend(range(start, end + 1))
                miss_map[fname] = nums
    return cov_map, miss_map
