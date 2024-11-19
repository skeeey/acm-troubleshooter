# coding: utf-8

import os
import subprocess
import tempfile
import time
import logging

logger = logging.getLogger(__name__)

def execute_commands(commands: str, need_to_approve=True, timeout=120) -> str:
    if need_to_approve:
        approve = input(f"👮 Approve to execute the below commands?\n{commands}\n(y/n) ")
        if approve.lower() != "y" and approve.lower() != "yes":
            exit(0)
    else:
        print(f"💻 Commands:\n{commands}")
    
    now = int(time.time())
    work_dir=tempfile.gettempdir()
    cmd_file = os.path.join(work_dir, f"acm_troubleshooting_code_{now}.sh")
    with open(cmd_file, "w", encoding="utf-8") as f:
        f.write(commands)
    
    logger.debug("cmd_file=%s", cmd_file)

    cmd_output = ""
    cmd = ["sh", cmd_file]
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=float(timeout),
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        cmd_output += "commands execution timeout"
        logger.warning("exitcode=124, %s execution timeout", cmd_file)
        return cmd_output
    
    cmd_output += result.stderr
    cmd_output += result.stdout
    exit_code = result.returncode
    if exit_code != 0:
        logger.warning("exitcode=%d, cmd=%s, output=%s", exit_code, cmd_file, cmd_output)
    
    print(f"Exit Code: {exit_code}\nOutputs:\n{cmd_output}")
    
    time.sleep(float(5))
    return cmd_output
