# GitHub Commit & Contributor Evaluation Tool

The **GitHub Commit & Contributor Evaluation Tool** is a Python CLI utility designed to analyze a public GitHub repository and generate two CSV reports: one with commit-level metrics and another with contributor-level metrics. It helps assess repository code quality and contributor performance.

## Tech Stack
- Python 3.8+
- GitPython
- Flake8
- pytest + coverage.py
- pandas

## Setup
```
git clone https://github.com/ShardulAswale/AI_Repo_Checker.git
cd AI_Repo_Checker
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage
```
python main.py <repo_url> [-n N] [-o OUTPUT_PREFIX]
```
- `<repo_url>`: HTTPS or SSH URL of the GitHub repo to analyze
- `-n, --num-commits`: Number of recent commits to include (default: 10)
- `-o, --output-prefix`: Prefix for the output CSV files (default: report)

### Examples
```
python cli.py https://github.com/owner/myrepo.git
python cli.py https://github.com/owner/otherrepo.git -n 5 -o metrics
```

## Output
- `<OUTPUT_PREFIX>_commit_metrics.csv`
- `<OUTPUT_PREFIX>_contributor_metrics.csv`

## Testing
```
pytest
```

---

📌 **Developed by [Shardul Aswale](https://github.com/ShardulAswale)**
