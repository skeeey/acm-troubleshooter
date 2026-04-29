import os

from git import Repo

from v2.server.tools.git import clone_repo, pull_repo, get_head_commit, parse_repo_name


def test_clone_repo(origin_repo, tmp_path):
    clone_path = str(tmp_path / "clone")
    repo = clone_repo(url=str(origin_repo), path=clone_path, branch="main", depth=1)

    assert os.path.exists(os.path.join(clone_path, "doc.md"))
    assert repo.head.commit.message == "initial commit"


def test_pull_repo(origin_repo, tmp_path):
    clone_path = str(tmp_path / "clone")
    clone_repo(url=str(origin_repo), path=clone_path, branch="main", depth=1)

    origin = Repo(origin_repo)
    new_file = origin_repo / "new.md"
    new_file.write_text("# New file")
    origin.index.add(["new.md"])
    origin.index.commit("add new file")

    pull_repo(path=clone_path)

    assert os.path.exists(os.path.join(clone_path, "new.md"))


def test_get_head_commit(origin_repo, tmp_path):
    clone_path = str(tmp_path / "clone")
    repo = clone_repo(url=str(origin_repo), path=clone_path, branch="main", depth=1)

    commit = get_head_commit(path=clone_path)
    assert len(commit) == 7
    assert repo.head.commit.hexsha.startswith(commit)


def test_parse_repo_name():
    assert parse_repo_name("https://github.com/org/repo.git") == "org-repo"
    assert parse_repo_name("https://github.com/org/repo") == "org-repo"
    assert parse_repo_name("https://github.com/stolostron/rhacm-docs.git") == "stolostron-rhacm-docs"
