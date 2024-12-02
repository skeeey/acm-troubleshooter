# coding: utf-8

import os
import logging
import subprocess
from urllib.parse import urlparse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CMDResult(BaseModel):
    return_code: int
    stdout: str
    stderr: str

def parse_repo(repo: str):
    url_result = urlparse(repo)
    dot_git_index = url_result.path.index('.git')
    return url_result.path[1:dot_git_index].replace("/", "-")

def clone(repo: str, cwd: str, dist: str, branch="main", timeout=120):
    cmds = ["git", "clone", f"--branch={branch}", "--depth=1", repo, dist]
    return run_commands(cmds=cmds, cwd=cwd, timeout=timeout)

def pull(cwd: str, timeout=120):
    cmds = ["git", "pull"]
    return run_commands(cmds=cmds, cwd=cwd, timeout=timeout)

def fetch_head_commit(cwd: str, timeout=120):
    cmds = ['git', '--no-pager', 'log', '--pretty=format:%h', '-n1']
    return run_commands(cmds=cmds, cwd=cwd, timeout=timeout)

def run_commands(cmds, cwd, timeout):
    try:
        result = subprocess.run(
            cmds,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=float(timeout),
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        logger.error("failed to run cmds `%s`, timeout", " ".join(cmds))
        return CMDResult(return_code=124, stdout="", stderr="timeout")
    if result.returncode != 0:
        logger.error("failed to run cmds `%s`, %s", " ".join(cmds), result.stderr)
    return CMDResult(return_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
  