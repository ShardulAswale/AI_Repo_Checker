# tests/test_lint.py

import tempfile
import os
import pytest
from lint import run_pylint_on_file

def test_run_pylint_on_file(tmp_path):
    # create a file with a lint issue: missing docstring and unused variable
    py = tmp_path / "bad.py"
    py.write_text("x=1\n\ndef foo():\n    return x\n")
    output = run_pylint_on_file(str(py.name), str(tmp_path))
    # should contain a missing‐docstring code and possibly unused‐variable
    assert "missing-module-docstring" in output or "missing-function-docstring" in output
