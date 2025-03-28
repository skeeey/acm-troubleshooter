# coding: utf-8

import re
import json
import logging

logger = logging.getLogger(__name__)

def post_msg(client, channel_id, timestamp, text):
    try:
        return client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=timestamp,
        )
    except Exception as e:
        logger.error(f"Error adding emoji reaction: {e}")

def add_emoji(client, channel_id, timestamp, emoji_name):
    try:
        return client.reactions_add(
            channel=channel_id,
            timestamp=timestamp,
            name=emoji_name
        )
    except Exception as e:
        logger.error(f"Error adding emoji reaction: {e}")

def get_thread_messages(client, channel_id, msg_ts):
    thread_ts = get_thread_ts(client, channel_id, msg_ts)
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

def get_thread_ts(client, channel_id, msg_ts):
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

def to_dialogue_context(msgs):
    dialogues = []
    for msg in msgs[0:len(msgs)-1]:
        user = msg["user"]
        text = msg["text"]
        dialogue = f"user_{user}: {text}"
        dialogues.append(dialogue)
    return "\n".join(dialogues)

def split_resp(resp):
    logger.info(resp)
    thinking = re.findall(r'<think>(.*?)</think>', resp, flags=re.DOTALL)
    text = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
    return thinking, text

def extract_json(text):
    json_pattern = re.compile(r'\{.*?\}')
    matches = json_pattern.findall(text)

    json_objects = []
    for match in matches:
        try:
            json_obj = json.loads(match)
            json_objects.append(json_obj)
        except json.JSONDecodeError as e:
            logger.error(f"cannot decode json str: {match}, {e}")
    return json_objects

def get_squad_channel(squad):
    if squad == "hypershift":
        return "#project-hypershift"
    return f"#forum-{squad}"

def reply(client, channel_id, timestamp, msg, llm_resp):
    if msg == "runbook":
        _, result = split_resp(llm_resp)
        response = post_msg(client, channel_id, timestamp, f"*Runbook*\n{result}")
    elif msg == "triage":
        _, result = split_resp(llm_resp)
        objs = extract_json(result)
        squads = []
        for obj in objs:
            for s in obj["squads"]:
                squads.append(get_squad_channel(s))
        text = ", ".join(squads)
        response = post_msg(client, channel_id, timestamp, f"Suggest to ask in {text}")
    elif msg == "suggest":
        asst_resp=llm_resp["response"],
        reason=llm_resp["reasoning"],
        references = "\n".join(llm_resp["relevant_doc_names"])
        text = f"*Response*\n{asst_resp[0]}\n*Reasoning*\n{reason[0]}\n*References*\n{references}"
        response = post_msg(client, channel_id, timestamp, text)
    else:
        asst_resp=llm_resp["response"],
        reason=llm_resp["reasoning"],
        references = "\n".join(llm_resp["relevant_doc_names"])
        text = f"*Response*\n{asst_resp[0]}\n*Reasoning*\n{reason[0]}\n*References*\n{references}"
        response = post_msg(client, channel_id, timestamp, text)
    add_emoji(client, channel_id, response["ts"], "thumbsup")
    add_emoji(client, channel_id, response["ts"], "thumbsdown")
