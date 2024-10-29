# coding: utf-8

import os
import logging
import time
import autogen
import click
from autogen.coding import LocalCommandLineCodeExecutor
# from autogen.agentchat.contrib.capabilities.text_compressors import LLMLingua
# from autogen.agentchat.contrib.capabilities.transforms import TextMessageCompressor
from dotenv import load_dotenv
from tools.loader import load_runbooks
from prompts.templates import PLANNER_PROMPT, ANALYST_PROMPT

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

load_dotenv()

logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.realpath(__file__))
work_dir=os.path.join(current_dir, "__workspace__")

llm_config = {
    "config_list": [
        {
            "model": "llama-3.1-70b-versatile",
            "api_key": os.getenv("GROQ_API_KEY"),
            "api_type": "groq",
            "temperature": 0.0,
            "price": [0, 0],
        }
    ]
}

# llm_config = {
#     "config_list": [
#         {
#             "model": "qwen2.5:14b",
#             "api_key": "NotRequired",
#             "base_url": "http://localhost:11434/v1",
#             "price": [0, 0],
#         }
#     ],
#     "cache_seed": None,
# }

def user_agent(human_input_mode):
    return autogen.UserProxyAgent(
        name="User",
        human_input_mode=human_input_mode,
        is_termination_msg=is_termination_message,
        code_execution_config=False,
    )

def planner_agent(llm_config, system_msg, human_input_mode):
    return autogen.AssistantAgent(
        name="Planner",
        description="Planner analyzes the User issues and creating diagnosis plan.",
        is_termination_msg=is_termination_message,
        human_input_mode=human_input_mode,
        llm_config=llm_config.copy(),
        system_message=system_msg,
    )

def analyst_agent(llm_config, system_msg, human_input_mode):
    return autogen.AssistantAgent(
        name="Analyst",
        description="Analyst analyzes the Planner's plan and converts the plan to executable command/scripts.",
        is_termination_msg=is_termination_message,
        human_input_mode=human_input_mode,
        llm_config=llm_config.copy(),
        system_message=system_msg,
    )

def executor_agent():
    return autogen.UserProxyAgent(
        name="Executor",
        description="Executor executes the code written by the Analyst and reports the result to Planner.",
        llm_config=False,
        code_execution_config={
            "executor": LocalCommandLineCodeExecutor(
                timeout=10,
                work_dir=work_dir,
            )
        },
        human_input_mode="NEVER",
    )

def selection(user, planner, analyst, executor, human_input_mode="NEVER"):
    def custom_speaker_selection_func(last_speaker, groupchat):
        content = groupchat.messages[-1]["content"]
        if "TERMINATE" in content:
            # print(content)
            return None

        if last_speaker == user:
            return planner
        if last_speaker == planner:
            wait(human_input_mode=human_input_mode)
            return analyst
        if last_speaker == analyst:
            return executor
        if last_speaker == executor:
            wait(human_input_mode=human_input_mode)
            return planner
        
        return None
    return custom_speaker_selection_func

def is_termination_message(msg):
    return msg.get("content") is not None and (msg.get("content", "").rstrip().endswith("TERMINATE"))

def wait(human_input_mode, wait_time=5):
     """Wait a while to avoid groq api qps limit 
     """
     if human_input_mode == "NEVER":
        time.sleep(wait_time)

@click.command()
@click.option("--runbooks", required=True, type=click.Path(file_okay=True, dir_okay=True, exists=True), help="the path of runbooks")
@click.option("--hub-mg", required=True, type=click.Path(file_okay=False, dir_okay=True, exists=True), help="the path of hub must-gather")
@click.option("--cluster-mg", type=click.Path(file_okay=False, dir_okay=True, exists=True), help="the path of managed cluster must-gather")
@click.option("--debug", is_flag=True, default=False, help="enable debug mode")
@click.option("--silent", is_flag=True, default=False, help="silent the agents")
@click.argument("issue")
def main(runbooks, hub_mg, cluster_mg, debug, silent, issue):
    human_input_mode = "NEVER"

    if cluster_mg is None:
        cluster_mg = hub_mg

    if debug is True:
        human_input_mode="ALWAYS"
    
    logger.debug("runbooks=%s,hub-must-gather=%s,managed-cluster-must-gather=%s", runbooks, hub_mg, cluster_mg)

    import nltk
    nltk.download('punkt_tab')
    nltk.download('averaged_perceptron_tagger_eng')
    
    runbook_contents = load_runbooks(runbooks)

    # TODO If the content is too large, try to compress the content
    # llm_lingua = LLMLingua()
    # text_compressor = TextMessageCompressor(text_compressor=llm_lingua)
    # compressed_contents = text_compressor.apply_transform([{"content": runbook_contents}])
    # logger.debug(compressed_contents)

    planner_prompt = PLANNER_PROMPT.format(context=runbook_contents)
    analyst_prompt = ANALYST_PROMPT.format(hub_dir=hub_mg, spoke_dir=cluster_mg)
    
    logger.debug(llm_config)
    logger.debug(planner_prompt)
    logger.debug(analyst_prompt)

    user = user_agent(human_input_mode)
    planner = planner_agent(llm_config, planner_prompt, human_input_mode)
    analyst = analyst_agent(llm_config, analyst_prompt, human_input_mode)
    executor = executor_agent()

    user.reset()
    planner.reset()
    analyst.reset()

    group_chat = autogen.GroupChat(
        agents=[user, planner, analyst, executor],
        max_round=50,
        messages=[],
        speaker_selection_method=selection(user, planner, analyst, executor, human_input_mode),
        send_introductions=True,
    )
    user.initiate_chat(
        autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config, silent=silent),
        message=issue,
    )

if __name__ == "__main__":
    main()
