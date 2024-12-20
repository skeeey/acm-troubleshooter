# coding: utf-8

"""
The git commands
"""

import logging
from urllib.parse import urlparse
from tools.common import run_commands

logger = logging.getLogger(__name__)

def parse_repo(repo: str):
    url_result = urlparse(repo)
    dot_git_index = url_result.path.index(".git")
    return url_result.path[1:dot_git_index].replace("/", "-")

def clone(repo: str, cwd: str, dist: str, branch="main", timeout=120):
    cmds = ["git", "clone", f"--branch={branch}", "--depth=1", repo, dist]
    return run_commands(cmds=cmds, cwd=cwd, timeout=timeout)

def pull(cwd: str, timeout=120):
    cmds = ["git", "pull"]
    return run_commands(cmds=cmds, cwd=cwd, timeout=timeout)

def fetch_head_commit(cwd: str, timeout=120):
    cmds = ["git", "--no-pager", "log", "--pretty=format:%h", "-n1"]
    return run_commands(cmds=cmds, cwd=cwd, timeout=timeout)
