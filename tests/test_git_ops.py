import pytest
from git import Repo
from src.git_ops import clone_repo, get_last_commits, checkout_commit
import os

def test_clone_and_commits(tmp_path):
    # 1) Create a dummy repo with two commits
    src = tmp_path / "src"
    src.mkdir()
    repo = Repo.init(str(src))

    f = src / "a.py"
    f.write_text("print('hello')\n")
    repo.index.add([str(f)])
    commit1 = repo.index.commit("initial commit")

    f.write_text("print('world')\n")
    repo.index.add([str(f)])
    commit2 = repo.index.commit("second commit")

    # 2) Clone it
    dest = tmp_path / "dest"
    cloned = clone_repo(str(src), str(dest))
    assert (dest / "a.py").exists()

    # 3) get_last_commits
    commits = get_last_commits(cloned, 2)
    shas = [c.hexsha for c in commits]
    assert shas == [commit2.hexsha, commit1.hexsha]

    # 4) checkout_commit
    checkout_commit(cloned, commit1.hexsha)
    assert (dest / "a.py").read_text() == "print('hello')\n"
