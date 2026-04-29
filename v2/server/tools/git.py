from urllib.parse import urlparse

from git import Repo


def clone_repo(url: str, path: str, branch: str = "main", depth: int = 1) -> Repo:
    return Repo.clone_from(url, path, branch=branch, depth=depth)


def pull_repo(path: str) -> None:
    repo = Repo(path)
    repo.remotes.origin.pull()


def get_head_commit(path: str) -> str:
    repo = Repo(path)
    return repo.head.commit.hexsha[:7]


def parse_repo_name(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.removesuffix(".git").strip("/")
    return path.replace("/", "-")
