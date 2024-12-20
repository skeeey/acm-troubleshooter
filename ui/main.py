# coding: utf-8

# pylint: disable=wrong-import-position,pointless-string-statement

"""
The UI of ACM troubleshooter service
"""

import os
import logging
import requests
import sys
import streamlit as st
from streamlit_feedback import streamlit_feedback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.chat import Request, Response, EvaluationRequest

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# server settings
server_url = "http://127.0.0.1:8000"

def send_req(chat_req: Request) -> Response:
    http_resp = requests.post(f"{server_url}/chat", data=chat_req.model_dump_json(), timeout=300)
    if http_resp.status_code == 200:
        return Response.model_validate_json(http_resp.content), None

    return None, f"failed to response, err=({http_resp.status_code}, {http_resp.content})"

def send_feedback(eval_req: EvaluationRequest):
    http_resp = requests.put(f"{server_url}/evaluation", data=eval_req.model_dump_json(), timeout=300)
    if http_resp.status_code == 200:
        return None

    logger.error("failed to send (score=%d, feedback=%s) for issue %s-%s, err=(%d,%s)",
                 eval_req.score, eval_req.feedback,
                 eval_req.issue_id, eval_req.resp_id,
                 http_resp.status_code, http_resp.content)
    return None

def show_asst_resp(chat_resp: Response):
    md = ["##### Reasoning", chat_resp.reasoning, "##### Response", chat_resp.resp]
    st.markdown("\n".join(md))

# start the web page
# TODO using st.sidebar to add configuration
st.set_page_config(page_icon="💬", layout="wide", page_title="ACM Assistant")

REMOVE_PADDING_FROM_SIDES="""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    div[data-testid="stToolbar"] {
        visibility: hidden;
        display: none;
    }
</style>
"""

st.markdown(REMOVE_PADDING_FROM_SIDES, unsafe_allow_html=True)

st.title("🤖 ACM Assistant")

"""
I'm an ACM assistant. I can help you to troubleshoot the ACM issues, for example,
troubleshoot why the status of the cluster cluster-a is unknown, or
troubleshoot why my addons are missing in my cluster cluster-b, etc. And I also can
answer the ACM questions, for example, what's the multicluster global hub? or
how to get the must-gather for multicluster global hub? etc.
"""

"""
Using /new to start a new question.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "What can I help with?"}
    ]

if "response" not in st.session_state:
    st.session_state["response"] = None

messages = st.session_state.messages
for msg in messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar= "🤖"):
            if isinstance(msg["content"], Response):
                show_asst_resp(msg["content"])
            else:
                st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"], avatar= "👨‍💻"):
            st.markdown(msg["content"])

if prompt := st.chat_input(placeholder="Message ACM Assistant"):
    if "/new" == str.strip(prompt).lower():
        st.session_state.clear()
        st.empty()
        st.rerun()

    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👨‍💻"):
        st.markdown(prompt)

    with st.spinner("Thinking ..."):
        req = Request(query=prompt)
        if st.session_state["response"] is not None:
            req.issue_id = st.session_state["response"].issue_id

        resp, err = send_req(chat_req=req)
        if err is not None:
            st.error(err)
            st.stop()

        st.session_state["response"] = resp
        with st.chat_message("assistant", avatar="🤖"):
            messages.append({"role": "assistant", "content": st.session_state["response"]})
            show_asst_resp(st.session_state["response"])

if st.session_state["response"]:
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="[Optional] Please provide an explanation",
        key=f"feedback_{len(messages)}",
    )

    if feedback:
        issue_id = st.session_state["response"].issue_id
        resp_id = st.session_state["response"].resp_id
        score = -1
        if feedback["score"] == "👍":
            score = 1

        send_feedback(EvaluationRequest(issue_id=issue_id, resp_id=resp_id, score=score, feedback=feedback["text"]))
        st.toast("Thanks your feedback!", icon="🙏")
