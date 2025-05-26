import pytest
from lint import run_pylint_on_file
import tempfile
import os

def test_run_pylint_on_file(tmp_path):
    # Create a file with a lint error: missing docstring
    f = tmp_path / "bad.py"
    f.write_text("x = 1\n")
    output = run_pylint_on_file("bad.py", str(tmp_path))
    assert "missing-module-docstring" in output or "missing-function-docstring" in output
