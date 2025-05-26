import os
from src.lint_ops import count_lint_issues

def test_count_lint_issues_detects_trailing_whitespace(tmp_path):
    repo = tmp_path
    f = repo / "bad.py"
    # line with trailing spaces + blank line
    f.write_text("x = 1  \n\n")
    # Should report at least one E/W/F/C issue
    issues = count_lint_issues("bad.py", str(repo))
    assert issues >= 1
