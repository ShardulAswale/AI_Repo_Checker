import pytest
from code_coverage import parse_coverage

@pytest.fixture
def sample_report():
    return (
        "Name           Stmts   Miss  Cover   Missing\n"
        "----------------------------------------------\n"
        "file1.py           5      2    60%   10-11,15\n"
        "file2.py           3      0   100%   -\n"
        "TOTAL              8      2    75%   -\n"
    )

def test_parse_coverage(sample_report):
    cov_map, miss_map = parse_coverage(sample_report)
    assert cov_map["file1.py"] == 60.0
    assert miss_map["file1.py"] == [10, 11, 15]
    assert cov_map["file2.py"] == 100.0
    assert miss_map["file2.py"] == []
