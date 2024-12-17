# coding: utf-8

import os
import re
import subprocess
import tiktoken
from pydantic import BaseModel

class CMDResult(BaseModel):
    return_code: int
    stdout: str
    stderr: str

def is_empty(s: str) -> bool:
    if not s:
        return True
    
    striped = replace_start(s, '"', '')
    striped = replace_end(striped, '"', '')

    if len(striped.strip()) == 0:
        return True

    return False

def replace_start(s: str, old_value: str, new_value: str):
    return re.sub(f'^{old_value}', new_value, s)

def replace_end(s: str, old_value: str, new_value: str):
    return re.sub(f'{old_value}$', new_value, s)

def count_tokens(text, encoding_name="cl100k_base"):
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

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
        return CMDResult(return_code=124, stdout="", stderr="timeout")
    
    return CMDResult(return_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
