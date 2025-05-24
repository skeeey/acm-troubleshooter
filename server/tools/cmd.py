# coding: utf-8

"""
The common helping functions
"""

import logging
import os
import re
import subprocess
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CMDResult(BaseModel):
    return_code: int
    stdout: str
    stderr: str

def run_commands(cmds, cwd, timeout):
    check_sanitize_command(" ".join(cmds))

    logger.debug("run commands %s", cmds)

    try:
        result = subprocess.run(
            cmds,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=float(timeout),
            env=os.environ.copy(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CMDResult(return_code=124, stdout="", stderr="timeout")

    return CMDResult(return_code=result.returncode, stdout=result.stdout, stderr=result.stderr)

def check_sanitize_command(code: str) -> None:
    dangerous_patterns = [
        (r"\brm\s+-rf\b", "Use of 'rm -rf' command is not allowed."),
        (r"\bmv\b.*?\s+/dev/null", "Moving files to /dev/null is not allowed."),
        (r"\bdd\b", "Use of 'dd' command is not allowed."),
        (r">\s*/dev/sd[a-z][1-9]?", "Overwriting disk blocks directly is not allowed."),
        (r":\(\)\{\s*:\|\:&\s*\};:", "Fork bombs are not allowed."),
    ]
    for pattern, message in dangerous_patterns:
        if re.search(pattern, code):
            raise ValueError(f"Potentially dangerous command detected: {message}")
