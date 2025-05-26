# coverage_ops.py

import logging
import os
from coverage import Coverage
import pytest

logger = logging.getLogger(__name__)

def measure_coverage(repo_path: str) -> dict[str, float]:
    """
    Run pytest under coverage for `repo_path`, then return a dict mapping each
    non-test .py file (relative to repo_path) to its coverage percentage.
    """
    repo_abs = os.path.abspath(repo_path)
    old_cwd = os.getcwd()
    os.chdir(repo_abs)

    cov = Coverage(
        source=[repo_abs],
        data_file=None,
        omit=[os.path.join(repo_abs, "tests", "*"), os.path.join(repo_abs, "test_*.py")]
    )
    cov.start()

    try:
        logger.info(f"Running pytest in {repo_abs} for coverage")
        pytest.main(["-q"])
    except Exception as e:
        logger.error(f"Coverage run failed: {e}")
    finally:
        cov.stop()
        cov.save()
        os.chdir(old_cwd)

    cov_map: dict[str, float] = {}
    data = cov.get_data()

    for measured in data.measured_files():
        m_abs = os.path.abspath(measured)
        if not m_abs.startswith(repo_abs) or not m_abs.endswith(".py"):
            continue
        rel = os.path.relpath(m_abs, repo_abs)
        if rel.startswith("tests" + os.sep) or rel.startswith("test_"):
            continue

        try:
            _, statements, missing, _ = cov.analysis(m_abs)
            total_stmts = len(statements)
            missed      = len(missing)
            pct = 0.0 if total_stmts == 0 else (total_stmts - missed) / total_stmts * 100
        except Exception as ex:
            logger.error(f"Error analyzing coverage for {rel}: {ex}")
            pct = 0.0

        cov_map[rel] = round(pct, 1)
        logger.debug(f"Coverage for {rel}: {pct:.1f}%")

    return cov_map

