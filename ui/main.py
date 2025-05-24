# coding: utf-8

# pylint: disable=wrong-import-position

"""
The UI of ACM troubleshooter service
"""

import os
import sys
import streamlit as st
import requests
from email_validator import validate_email, EmailNotValidError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server.schemas.user import Request, Response

# server settings
server_url = "http://127.0.0.1:8000/api"

def is_redhat_email(email):
    try:
        validated_email = validate_email(email, check_deliverability=False)
        if validated_email.domain == "redhat.com":
            return True
        else:
            return False
    except EmailNotValidError:
        return False


def create_user(name: str):
    req = Request(name=name)
    try:
        http_resp = requests.post(f"{server_url}/users/", data=req.model_dump_json(), timeout=30)
        if http_resp.status_code == 200:
            return Response.model_validate_json(http_resp.content), None
        return None, f"failed to create the user {name}, err=({http_resp.status_code}, {http_resp.content})"
    except requests.exceptions.Timeout:
        return None, "failed to send request timeout"
    except requests.exceptions.RequestException as e:
        return None, f"failed to send request {e}"


st.set_page_config(page_icon="💬", page_title="ACM Assistant", initial_sidebar_state="collapsed")

REMOVE_PADDING_FROM_SIDES="""
<style>
    div[data-testid="stToolbar"] {
        visibility: hidden;
        display: none;
    }
    div[data-testid="stSidebarCollapsedControl"] {
        display: none
    }
</style>
"""
st.markdown(REMOVE_PADDING_FROM_SIDES, unsafe_allow_html=True)
st.title("Welcome to ACM Assistant")

username = st.text_input("Email", placeholder="xxx@redhat.com")

if st.button("Log in", type="primary"):
    if is_redhat_email(username):
        user, err = create_user(username)
        if user is None:
            st.error(err)
        else:
            st.session_state.user = user
            st.switch_page("pages/chat.py")
    else:
        st.error("Incorrect email")
