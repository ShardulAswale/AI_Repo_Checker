# Repo Analyzer

## Overview
A CLI tool that clones a public GitHub repo, checks out a commit, and runs:
1. **Lint** (flake8)  
2. **Code Coverage** (pytest + coverage)  
3. **LLM Suggestions** (Together API)  
4. **All** of the above

## Setup
```bash
git clone <this_repo>
cd your_project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
