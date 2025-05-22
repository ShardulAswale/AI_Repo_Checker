# app.py

import streamlit as st
import os

from repo_analyzer import (
    clone_repo, get_commits, checkout_commit,
    list_python_files, run_linters_on_file
)
# from llm_analyzer import analyze_code_with_llm  # 👈 commented out for now

REPO_PATH = "repo"

st.title("🔍 Repo Commit Analyzer")

# --- Step 1: Clone the repo ---
repo_url = st.text_input("Enter GitHub Repository URL")
if st.button("Fetch Repo"):
    if not repo_url.strip():
        st.error("Please enter a valid GitHub URL.")
    else:
        with st.spinner("Cloning repository..."):
            try:
                clone_repo(repo_url)
                st.success(f"Cloned into `{REPO_PATH}/`.")
                for k in ("commits", "py_files"):
                    st.session_state.pop(k, None)
            except Exception as e:
                st.error(f"Clone failed: {e}")

# --- Step 2: Fetch commits with metadata ---
if os.path.isdir(REPO_PATH):
    if st.button("Fetch Commits"):
        with st.spinner("Getting last 10 commits..."):
            try:
                commits = get_commits()
                st.session_state["commits"] = commits
                st.success("Commits fetched — choose one below.")
            except Exception as e:
                st.error(f"Could not fetch commits: {e}")

# --- Step 3: Select commit & list files ---
if "commits" in st.session_state:
    # build a map for display
    commit_map = {c["hash"]: c for c in st.session_state["commits"]}
    selected_hash = st.selectbox(
        "Select a Commit",
        options=[c["hash"] for c in st.session_state["commits"]],
        format_func=lambda h: f"{h[:7]} — {commit_map[h]['author']} on {commit_map[h]['date']}"
    )
    if st.button("Checkout & List Files"):
        with st.spinner(f"Checking out {selected_hash[:7]}..."):
            try:
                checkout_commit(selected_hash)
                files = list_python_files()
                st.session_state["py_files"] = files
                st.success(f"Found {len(files)} Python files.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- Step 4: Select files & analyze lint only ---
if "py_files" in st.session_state:
    selected = st.multiselect("Select files to lint", st.session_state["py_files"])
    if st.button("Run Lint on Selected"):
        if not selected:
            st.warning("Select at least one file.")
        else:
            for fpath in selected:
                st.subheader(f"Lint Results for `{fpath}`")
                lint = run_linters_on_file(fpath)
                st.code(lint, language="bash")
                # st.markdown("**LLM Feedback:**")
                # code = open(os.path.join(REPO_PATH, fpath)).read()
                # st.write(analyze_code_with_llm(code))
