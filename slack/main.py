# coding: utf-8

"""
The server of Slack bot
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core import Settings
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from embeddings.huggingface import BGE
from models.contexts import LLMConfig, RetrievalConfig
from services.llm import LLMService
from services.index import RAGService
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack.llm import openai_call
from slack.utils import get_thread_messages, to_dialogue_context, post_msg, reply
from slack.prompt import system_prompt, runbook_template, squad_template

# load envs
load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# rag settings
Settings.llm = None
Settings.context_window = 10240 # maximum input size to the LLM
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]
# TODO use the latest doc sources
doc_sources = os.getenv("DOC_SOURCES").split(",")

# default llm settings
llm_model=os.getenv("LM_MODEL")
llm_api_base=os.getenv("LM_API_BASE")
llm_api_key=os.getenv("LM_API_KEY")

rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
llm_svc = LLMService(rag_svc=rag_svc)

#################################################
# join the slack channel and handle mention event
#################################################
slack_token=os.environ.get("SLACK_BOT_TOKEN")
channel_name="bot-test"

app = App(
   token=slack_token,
   signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
app_handler = SlackRequestHandler(app)

channel_list = app.client.conversations_list().data
channel = next((channel for channel in channel_list.get('channels') if channel.get("name") == channel_name), None)
channel_id = channel.get('id')
app.client.conversations_join(channel=channel_id)
logger.info(f"Join the channel {channel_id}")

@app.event("app_mention")
def handle_app_mentions(event, client):
    channel = event["channel"]
    msg_ts = event["event_ts"]
    text = event["text"].split(" ")
    msg = (" ".join(text[1:])).strip()
    logger.info("channel=%s,msg_ts=%s,msg=%s", channel, msg_ts, msg)

    post_msg(client, channel, msg_ts, "Thinking...")

    if msg == "runbook":
        dialogue = to_dialogue_context(get_thread_messages(client, channel, msg_ts))
        llm_resp = openai_call(system_prompt, runbook_template.format(dialogue=dialogue))
        reply(client, channel, msg_ts, msg, llm_resp)
    elif msg == "triage":
        # TODO add dialogue context
        issue = get_thread_messages(client, channel, msg_ts)[0]["text"]
        llm_resp = openai_call(system_prompt, squad_template.format(issue=issue))
        reply(client, channel, msg_ts, msg, llm_resp)
    elif msg == "suggest":
        # TODO add dialogue context
        issue = get_thread_messages(client, channel, msg_ts)[0]["text"]
        llm_resp = llm_svc.response(
            mcfg=LLMConfig(model=llm_model, api_base=llm_api_base, api_key=llm_api_key),
            rcfg=RetrievalConfig(doc_sources=doc_sources),
            query=issue,
            history_resps=[]
        )
        reply(client, channel, msg_ts, msg, llm_resp)
    else:
        issue = get_thread_messages(client, channel, msg_ts)[0]["text"]
        llm_resp = llm_svc.response(
            mcfg=LLMConfig(model=llm_model, api_base=llm_api_base, api_key=llm_api_key),
            rcfg=RetrievalConfig(doc_sources=doc_sources),
            query=issue,
            history_resps=[]
        )
        reply(client, channel, msg_ts, msg, llm_resp)

@app.event("message")
def handle_message(body, say):
    pass

##################
# start api server
##################
server = FastAPI()
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@server.post("/")
async def endpoint(request: Request):
    data = await request.json()
    if "challenge" in data:
        return {"challenge": data["challenge"]}
    return await app_handler.handle(request)
