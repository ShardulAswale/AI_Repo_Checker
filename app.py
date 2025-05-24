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

REPO_DIR = "repo"

st.set_page_config(page_title="Repo Analyzer", layout="wide")
st.title("🔍 Repo Analyzer: Diff • Pylint • Coverage")

# — Step 1: Clone Repo —
repo_url = st.text_input("GitHub Repo URL", placeholder="https://github.com/owner/repo")
if st.button("🔄 Clone Repo", key="clone_repo"):
    if not repo_url.strip():
        st.error("Enter a valid GitHub URL.")
    else:
        try:
            clone_repo(repo_url, REPO_DIR)
            st.success("✅ Repo cloned.")
            for key in ("branches", "commits", "files", "commit"):
                st.session_state.pop(key, None)
        except Exception as e:
            st.error(f"Clone failed: {e}")

# — Step 2: Branch picker —
if os.path.isdir(REPO_DIR):
    if "branches" not in st.session_state:
        try:
            st.session_state["branches"] = get_branches(REPO_DIR)
        except Exception as e:
            st.error(f"Could not list branches: {e}")

if "branches" in st.session_state:
    branch = st.selectbox("Branch", st.session_state["branches"], key="branch_select")
    if st.button("🔀 Switch Branch", key="switch_branch"):
        try:
            checkout_branch(branch, REPO_DIR)
            st.success(f"Switched to branch `{branch}`")
            for key in ("commits", "files", "commit"):
                st.session_state.pop(key, None)
        except Exception as e:
            st.error(f"Branch checkout failed: {e}")

# — Step 3: Fetch commits —
if os.path.isdir(REPO_DIR) and st.button("📜 Fetch Commits", key="fetch_commits"):
    try:
        st.session_state["commits"] = get_commits(repo_path=REPO_DIR)
        st.success(f"Fetched {len(st.session_state['commits'])} commits on `{branch}`")
    except Exception as e:
        st.error(f"Fetch commits failed: {e}")

# — Step 4: Select commit & list changed .py files —
if "commits" in st.session_state:
    commits = st.session_state["commits"]
    commit_map = {c["hash"]: c for c in commits}

    selected_hash = st.selectbox(
        "Commit",
        [c["hash"] for c in commits],
        format_func=lambda h: f"{h[:7]} — {commit_map[h]['message']}",
        key="commit_select"
    )
    if st.button("🔀 Show Changed .py Files", key="show_files"):
        try:
            checkout_commit(selected_hash, REPO_DIR)
            st.session_state["commit"] = selected_hash
            changes = list_changed_python_files(selected_hash, REPO_DIR)
            if not changes:
                st.warning("No Python files changed in this commit.")
            else:
                st.session_state["files"] = changes
                st.success(f"Found {len(changes)} changed .py files")
        except Exception as e:
            st.error(f"Error listing changed files: {e}")

# — Step 5: Tabs for Diff, Pylint, Coverage —
if "files" in st.session_state and "commit" in st.session_state:
    file_sel = st.selectbox("File", st.session_state["files"], key="file_select")
    tabs = st.tabs(["Diff", "Pylint", "Coverage"])

    # ---- Diff Tab ----
    with tabs[0]:
        st.markdown("#### Full Diff")
        diff = subprocess.check_output(
            ["git", "show", st.session_state["commit"], "--", file_sel],
            cwd=REPO_DIR
        ).decode()
        st.code(diff, language="diff")

    # ---- Pylint Tab ----
    with tabs[1]:
        st.markdown("#### Pylint Report")
        pylint_out = run_pylint_on_file(file_sel, REPO_DIR)
        with st.expander("Show Pylint output", expanded=False, key="pylint_expander"):
            st.code(pylint_out, language="text")

    # ---- Coverage Tab ----
    with tabs[2]:
        st.markdown("#### Raw Coverage Report")
        report = run_code_coverage(REPO_DIR)
        st.code(report or "∅ (empty report)", language="text")

        st.markdown("#### Coverage Summary")
        if not report.strip() or report.startswith("[Coverage Error]"):
            st.warning("No tests found or coverage run failed → 0% coverage.")
            st.metric("Coverage %", "0.0%", key="cov_metric_zero")
        else:
            cov_map, miss_map = parse_coverage(report)
            pct = cov_map.get(file_sel, 0.0)
            st.metric("Coverage %", f"{pct:.1f}%", key="cov_metric")
            if pct == 100.0:
                st.success("✔️ Fully covered")
            else:
                missing = miss_map.get(file_sel, [])
                if missing:
                    st.markdown("**Missing lines:**")
                    st.write(", ".join(map(str, missing)))
                else:
                    st.info("No missing lines reported (coverage < 100%).")

# — Step 6: Compile Full Report Across All Commits —
if os.path.isdir(REPO_DIR):
    if st.button("📊 Compile Full Report", key="compile_report"):
        commits = get_commits(repo_path=REPO_DIR)  # always re-fetch
        rows = []
        seen = set()

        with st.spinner("Generating report across all commits…"):
            for c in commits:
                ch = c["hash"]
                checkout_commit(ch, REPO_DIR)

                files = [
                    f for f in list_changed_python_files(ch, REPO_DIR)
                    if f.endswith(".py") and not f.startswith(("tests/", "test_"))
                ]

                for f in files:
                    key = (ch, f)
                    if key in seen:
                        continue
                    seen.add(key)

                    po = run_pylint_on_file(f, REPO_DIR)
                    lint_count = len([
                        L for L in po.splitlines()
                        if L and not L.startswith("Your code has been rated")
                    ])

                    cr = run_code_coverage(REPO_DIR)
                    cov_map, _ = parse_coverage(cr)
                    pct = cov_map.get(f, 0.0)

                    rows.append({
                        "commit":      ch[:7],
                        "author":      c["author"],
                        "date":        c["date"],
                        "file":        f,
                        "lint_issues": lint_count,
                        "coverage_%":  pct
                    })

        if rows:
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            st.subheader("📈 Full Commit Report")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Full Report CSV",
                data=csv,
                file_name="full_commit_report.csv",
                mime="text/csv",
                key="download_report"
            )
        else:
            st.warning("No data to report—make sure you’ve fetched commits first.")
