# streamlit_app.py

import streamlit as st
import os
import subprocess
import pandas as pd

from git_fetch import (
    clone_repo,
    get_branches,
    checkout_branch,
    get_commits,
    checkout_commit,
    list_changed_python_files
)
from lint import run_pylint_on_file
from code_coverage import run_code_coverage, parse_coverage
from report import generate_committer_report

REPO_DIR = "repo"

def list_all_python_files(repo_path: str) -> list[str]:
    py_files = []
    for root, dirs, files in os.walk(repo_path):
        # skip .git directory
        if ".git" in dirs:
            dirs.remove(".git")
        for fn in files:
            if fn.endswith(".py"):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, repo_path)
                py_files.append(rel)
    return sorted(py_files)

st.set_page_config(page_title="Repo Analyzer", layout="wide")
st.title("🔍 Repo Analyzer: Diff • Pylint • Coverage")

# Step 1: Clone / Reset
repo_url = st.text_input("GitHub Repo URL", placeholder="https://github.com/owner/repo", key="url_input")
if st.button("🔄 Clone / Reset Repo", key="btn_clone"):
    if not repo_url:
        st.error("Please enter a repository URL.")
    else:
        try:
            clone_repo(repo_url, REPO_DIR)
            st.success("Repository cloned/reset to ./repo")
            for k in ("branches","commits","files","commit","all_files"):
                st.session_state.pop(k, None)
        except Exception as e:
            st.error(f"Clone failed: {e}")

# Step 2: Branch Picker
if os.path.isdir(REPO_DIR):
    if "branches" not in st.session_state:
        try:
            st.session_state["branches"] = get_branches(REPO_DIR)
        except Exception as e:
            st.error(f"Error listing branches: {e}")

    if "branches" in st.session_state:
        branch = st.selectbox("Select branch", st.session_state["branches"], key="branch_sel")
        if st.button("🔀 Checkout Branch", key="btn_checkout"):
            try:
                checkout_branch(branch, REPO_DIR)
                st.success(f"Checked out `{branch}`")
                for k in ("commits","files","commit","all_files"):
                    st.session_state.pop(k, None)
            except Exception as e:
                st.error(f"Branch checkout failed: {e}")

# Step 3: Fetch Commits (last 10)
if os.path.isdir(REPO_DIR) and st.button("📜 Fetch Commits", key="btn_fetch"):
    try:
        st.session_state["commits"] = get_commits(repo_path=REPO_DIR)
        st.success(f"Fetched {len(st.session_state['commits'])} commits")
    except Exception as e:
        st.error(f"Fetch commits failed: {e}")

# Step 4: Select Commit & List Changed Files
if "commits" in st.session_state:
    commits = st.session_state["commits"]
    cmap = {c["hash"]: c for c in commits}

    selected = st.selectbox(
        "Select commit",
        [c["hash"] for c in commits],
        format_func=lambda h: f"{h[:7]} – {cmap[h]['message']}",
        key="commit_sel"
    )
    if st.button("📂 List Changed .py Files", key="btn_list"):
        try:
            checkout_commit(selected, REPO_DIR)
            st.session_state["commit"] = selected
            # still store changed for reference if you like
            st.session_state["files"] = list_changed_python_files(selected, REPO_DIR)
            # but also populate ALL python files
            st.session_state["all_files"] = list_all_python_files(REPO_DIR)
            st.success(f"{len(st.session_state['files'])} changed files, {len(st.session_state['all_files'])} total .py files")
        except Exception as e:
            st.error(f"Error listing files: {e}")

# Step 5: Diff • Pylint • Coverage Tabs
if "all_files" in st.session_state and "commit" in st.session_state:
    fsel = st.selectbox("Select file", st.session_state["all_files"], key="file_sel")
    tabs = st.tabs(["Diff", "Pylint", "Coverage"])

    # Diff Tab
    with tabs[0]:
        st.markdown("#### Full Diff")
        diff = subprocess.check_output(
            ["git", "show", st.session_state["commit"], "--", fsel],
            cwd=REPO_DIR
        ).decode()
        st.code(diff, language="diff")

    # Pylint Tab
    with tabs[1]:
        st.markdown("#### Pylint Report")
        pout = run_pylint_on_file(fsel, REPO_DIR)
        st.code(pout, language="text")

    # Coverage Tab
    with tabs[2]:
        st.markdown("#### Raw Coverage Report")
        report = run_code_coverage(REPO_DIR)
        st.code(report or "∅ (empty report)", language="text")

        st.markdown("#### Coverage Summary")
        if not report.strip() or report.startswith("[Coverage Error]"):
            st.warning("No tests found or coverage run failed → 0%")
            st.metric("Coverage %", "0.0%")
        else:
            cov_map, miss_map = parse_coverage(report)
            pct = cov_map.get(fsel, 0.0)
            st.metric("Coverage %", f"{pct:.1f}%")
            if pct == 100.0:
                st.success("✔️ Fully covered")
            elif miss_map.get(fsel):
                st.markdown("**Missing lines:** " + ", ".join(map(str, miss_map[fsel])))
            else:
                st.info("Coverage < 100%, but no missing lines reported.")

# Step 6: Generate Committer Report
st.markdown("---")
if os.path.isdir(REPO_DIR) and st.button("🔢 Generate Committer Report", key="btn_report"):
    if not repo_url:
        st.error("Please clone a repository first.")
    else:
        try:
            df = generate_committer_report(repo_url, local_dir=REPO_DIR)
            st.subheader("Committer Evaluation Report")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name="committer_report.csv",
                mime="text/csv",
                key="btn_download"
            )
        except Exception as e:
            st.error(f"Error generating report: {e}")
