import os
import logging
import dspy
from dotenv import load_dotenv
from graph.workflow import build_graph
from tools.loader import load_runbooks

load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

lm = dspy.LM('llama-3.1-70b-versatile', api_base='https://api.groq.com/openai/v1', api_key=os.getenv("GROQ_API_KEY"))
dspy.configure(lm=lm)

if __name__ == "__main__":
    documents = load_runbooks("/Users/wliu1/Workspace/foundation-docs")

    # graph = build_graph(
    #     documents=documents,
    #     hub_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-12962",
    #     spoke_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-12962",
    # )
    # graph.invoke({"issue": "the cluster local-cluster is unknown"}, config={"recursion_limit": 50})

    graph = build_graph(
        documents=documents,
        hub_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-13222",
        spoke_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-13222",
    )
    graph.invoke({"issue": "the addon application-manager is not installed in the cluster v-cw-1-1d"}, config={"recursion_limit": 50})

    # graph = build_graph(
    #     documents=documents,
    #     hub_must_gather_dir="/Users/wliu1/Downloads/must-gather-case-03926591/hub",
    #     spoke_must_gather_dir="/Users/wliu1/Downloads/must-gather-case-03926591/spoke",
    # )
    # graph.invoke({"issue": "cluster ocp-dev-01 is unknown"}, config={"recursion_limit": 50})

    # TODO
    # omc get managedclusters ocp002pm002400 -ojsonpath='{.metadata.labels}' | jq 'keys'
    # graph = build_graph(
    #     documents=documents,
    #     hub_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-14296",
    #     spoke_must_gather_dir="/Users/wliu1/Downloads/must-gather-acm-14296",
    # )
    # graph.invoke({"issue": "ACM observability grafana dashboard is empty"}, config={"recursion_limit": 50})
