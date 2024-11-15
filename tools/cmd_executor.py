import os
import logging
import subprocess
import tempfile
import time

logger = logging.getLogger(__name__)

def execute_commands(commands: str, timeout=120) -> str:
    now = int(time.time())
    work_dir=tempfile.gettempdir()
    cmd_file = os.path.join(work_dir, f"acm_troubleshooting_code_{now}.sh")
    with open(cmd_file, "w", encoding="utf-8") as f:
        f.write(commands)
    
    logger.debug("cmd_file=%s", cmd_file)

    logs_all = ""
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
        logs_all += "commands execution timeout"
        logger.warning("exitcode=124, %s execution timeout", cmd_file)
        return logs_all
    
    logs_all += result.stderr
    logs_all += result.stdout
    exit_code = result.returncode
    if exit_code != 0:
        logger.warning("exitcode=%d, cmd=%s, output=%s", exit_code, cmd_file, logs_all)
    
    return logs_all