import logging

import dspy
from dotenv import load_dotenv

from tools.loader import load_runbooks
from tools.cmd_executor import execute_commands

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

load_dotenv()

logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

#lm = dspy.LM('llama-3.1-70b-versatile', api_base='https://api.groq.com/openai/v1', api_key=os.getenv("GROQ_API_KEY"))
lm = dspy.LM('ollama_chat/qwen2.5:32b', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)


issue = "the local-cluster is unknown"

plan = dspy.ChainOfThought('runbooks, issue -> troubleshooting_plan')
result = plan(runbooks=load_runbooks(dir="/Users/wliu1/Workspace/foundation-docs"), issue=issue)
print(result)

# convert = dspy.ChainOfThought("troubleshooting_plan -> commands")
# print(convert(troubleshooting_plan=result))


# notes="""
# - Do not generate delete/create/update/apply/patch in shell commands.
# - Do not generate if-else statements in shell commands.
# - Only output shell commands.
# - Use omc instead of oc or kubectl.
# - If the cluster name is 'local-cluster,' initialize the omc command with omc use <hub_must_gather_dir>.
# - If the commands will run in the hub cluster, use omc use <hub_must_gather_dir>.
# - If the commands will run in a managed cluster, initialize the omc command with omc use <spoke_must_gather_dir>.
# - If the cluster name is 'local-cluster', its klusterlet is running in the hub cluster.
# """

class Executor(dspy.Signature):
    """Convert a troubleshooting plan to executable commands, and then execute them.

    - Do not generate delete/create/update/apply/patch in shell commands.
    - Do not generate if-else statements in shell commands.
    - Use omc instead of oc or kubectl.
    - If the cluster name is 'local-cluster', initialize the omc command with `omc use <hub_must_gather_dir>`.
    - If the commands will run in the hub cluster, use omc use <hub_must_gather_dir>.
    - If the commands will run in a managed cluster, initialize the omc command with `omc use <spoke_must_gather_dir>`.

    Example:

    Plan:
    Check the ManagedClusterConditionAvailable condition for managed cluster cluster1 on a hub cluster:
    `oc get managedcluster cluster1 -ojsonpath='{{.status.conditions[?(@.type=="ManagedClusterConditionAvailable")].status}}'`

    Output Commands:
    ocm use /home/user1/hub
    available_status=$(omc get managedcluster cluster1 -ojsonpath='{{.status.conditions[?(@.type=="ManagedClusterConditionAvailable")].status}}')
    echo "ManagedClusterConditionAvailable for cluster1: $available_status"
    """

    troubleshooting_plan: str = dspy.InputField(desc="The troubleshooting plan")
    hub_must_gather_dir: str = dspy.InputField(desc="The hub must-gather dir")
    spoke_must_gather_dir: str = dspy.InputField(desc="The spoke must-gather dir")

    execution_result: str = dspy.OutputField()

execute = dspy.ReAct(Executor, tools=[execute_commands])
print(execute(
    #notes=notes,
    troubleshooting_plan=result["troubleshooting_plan"],
    hub_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-12962",
    spoke_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-12962",
))