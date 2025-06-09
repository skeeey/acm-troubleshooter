# coding: utf-8

"""
The service for slack

1. Generate a runbook from a dialogue.
2. Find suitable squads to assign the given issue
3. Give a suggestion for the user's question based on ACM docs
4. (TODO) Chat with the bot to resolve the issue in complex scenario
    - Access the third system to get more info, e.g. JIRA/support cases/code repo
    - Analyze the must-gather
    - Analyze the user's screenshot/vidoe
    - etc
"""

import logging
import os
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from server.services.workflow import WorkflowService
from server.tools.llm import gen_runbook, assign_squads

logger = logging.getLogger(__name__)

class SlackService:
    def __init__(self, workflow_svc: WorkflowService):
        self.app = App(
            token=os.getenv("SLACK_BOT_TOKEN"),
            signing_secret=os.getenv("SLACK_SIGNING_SECRET")
        )
        self.workflow_svc = workflow_svc
        self.channel_name = os.getenv("SLACK_CHANNEL_NAME")
        self.channel_id = None
        self.handler = SlackRequestHandler(self.app)
        self.join_channel()
        self.register_handlers()
        logger.info("Slack service is initialized")

    def handle_request(self, req):
        self.handler.handle(req)

    def register_handlers(self):
        @self.app.event("app_mention")
        def handle_app_mentions(event, client):
            channel = event["channel"]
            msg_ts = event["event_ts"]
            text = event["text"].split(" ")
            msg = (" ".join(text[1:])).strip()
            logger.info("channel=%s,msg_ts=%s,msg=%s", channel, msg_ts, msg)

            self.post_msg(client, channel, msg_ts, "Thinking...")

            # TODO add evaluation emoji
            # self.add_emoji(client, channel_id, response["ts"], "thumbsup")
            # self.add_emoji(client, channel_id, response["ts"], "thumbsdown")
            if msg == "runbook":
                dialogue_ctx = self.to_dialogue_context(self.get_thread_messages(client, channel, msg_ts))
                runbook = gen_runbook(dialogue_ctx)
                self.post_msg(client, channel, msg_ts, f"*Runbook*\n{runbook}")
            elif msg == "triage":
                # TODO add dialogue context
                issue = self.get_thread_messages(client, channel, msg_ts)[0]["text"]
                squads = assign_squads(issue)
                # TODO to_squad_channel
                self.post_msg(client, channel, msg_ts, f"{squads}")
            elif msg == "suggest":
                # TODO add dialogue context
                issue = self.get_thread_messages(client, channel, msg_ts)[0]["text"]
                resp = self.workflow_svc.run(issue, [])
                self.post_msg(client, channel, msg_ts, resp)
            else:
                self.post_msg(client, channel, msg_ts, f"unsupported command {msg}")

        @self.app.event("message")
        def handle_message(body, say):
            pass

    def join_channel(self):
        try:
            response = self.app.client.conversations_list()
            channels = response.data.get("channels", [])
            channel = next((c for c in channels if c.get("name") == self.channel_name), None)

            if channel:
                self.channel_id = channel["id"]
                self.app.client.conversations_join(channel=self.channel_id)
                logger.info(f"Joined the channel: {self.channel_id}")
            else:
                logger.warning(f"Channel '{self.channel_name}' not found.")
        except Exception as e:
            logger.error(f"Failed to join channel: {e}")

    def post_msg(self, client, channel_id, timestamp, text):
        try:
            return client.chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=timestamp,
            )
        except Exception as e:
            logger.error(f"Error adding emoji reaction: {e}")

    def add_emoji(self, client, channel_id, timestamp, emoji_name):
        try:
            return client.reactions_add(
                channel=channel_id,
                timestamp=timestamp,
                name=emoji_name
            )
        except Exception as e:
            logger.error(f"Error adding emoji reaction: {e}")

    def get_thread_messages(self, client, channel_id, msg_ts):
        thread_ts = self.get_thread_ts(client, channel_id, msg_ts)
        if thread_ts is None:
            logger.warning("thread ts is not found")
            return []
        try:
            msgs = []
            result = client.conversations_replies(channel=channel_id, ts=thread_ts)
            for msg in result["messages"]:
                msgs.append(msg)
            return msgs
        except Exception as e:
            logger.error(f"Error fetching message details: {e}")
            return []

    def get_thread_ts(self, client, channel_id, msg_ts):
        try:
            # Fetch the last message details
            response = client.conversations_history(
                channel=channel_id,
                latest=msg_ts,
                limit=1,
                inclusive=True,
            )
            messages = response.get("messages", [])
            if messages:
                message = messages[0]
                # If thread_ts doesn't exist, the message is the parent
                thread_ts = message.get("thread_ts", message["ts"])
                return thread_ts

            logger.error(f"No messages are found: channel={channel_id}, thread={msg_ts}")
            return None
        except Exception as e:
            logger.error(f"Error fetching message details: {e}")
            return None

    def to_dialogue_context(self, msgs):
        dialogues = []
        for msg in msgs[0:len(msgs)-1]:
            user = msg["user"]
            text = msg["text"]
            dialogue = f"user_{user}: {text}"
            dialogues.append(dialogue)
        return "\n".join(dialogues)

    def to_squad_channel(self, squad):
        if squad == "hypershift":
            return "#project-hypershift"
        return f"#forum-{squad}"
