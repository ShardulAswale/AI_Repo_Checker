import os
from pathlib import Path
import pytest
from src.coverage_ops import measure_coverage

def test_measure_coverage_empty(tmp_path, monkeypatch):
    # If no tests exist, returns empty map
    repo = tmp_path / "repo"
    repo.mkdir()
    # create a module without tests
    (repo / "mod.py").write_text("x = 1\n")
    cov = measure_coverage(str(repo))
    assert isinstance(cov, dict)
    assert cov == {}  # no tests → no data

def test_measure_coverage_simple(tmp_path, monkeypatch):
    # Create a simple repo with one file and one test
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a,b):\n    return a+b\n")
    tests = repo / "test_calc.py"
    tests.write_text(
        "from calc import add\n"
        "def test_add():\n"
        "    assert add(2,3) == 5\n"
    )
    cov = measure_coverage(str(repo))
    # Should report coverage for calc.py around 100%
    assert "calc.py" in cov
    assert cov["calc.py"] == pytest.approx(100.0, rel=1e-3)
