import sys
import os
import logging

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server.main import diagnose_issue, create_issue
from server.models import Request, Response


# log settings
LOG_DATE_FORMAT = "%H:%M:%S"
LOG_FORMAT = "%(asctime)s - [%(levelname)s] %(module)s/%(lineno)d: %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


st.set_page_config(page_icon="💬", layout="wide", page_title="ACM")


def hidden_default_menu():
    st.markdown(
        """
      <style>
          .reportview-container {
              margin-top: -2em;
          }
          #MainMenu {visibility: hidden;}
          .stAppDeployButton {display:none;}
          footer {visibility: hidden;}
          #stDecoration {display:none;}
      </style>
  """,
        unsafe_allow_html=True,
    )


def history_message():
    st.header(
        "Red Hat Advanced Cluster Management for Kubernetes",
        divider="rainbow",
        anchor=False,
    )

    # st.subheader(
    #     "Red Hat Advanced Cluster Management for Kubernetes",
    #     divider="rainbow",
    #     anchor=False,
    # )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    logging.info("the cached message size = %d", len(st.session_state.messages))

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        avatar = "🤖" if message["role"] == "assistant" else "👨‍💻"
        with st.chat_message(message["role"], avatar=avatar):
            if isinstance(message["content"], Response):
                st.markdown(message["content"].plan)
                st.markdown(message["content"].reasoning)
            else:
                st.markdown(message["content"])
            # st.markdown()


def interact():
    if prompt := st.chat_input("Put the ACM issue here..."):
        if "/clear" == str.strip(prompt).lower():
            logger.info("clean the current session")
            st.session_state.clear()
            return

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="👨‍💻"):
            st.markdown(prompt)

        try:
            # Use the generator function with st.write_stream
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner():
                    step_type = "create"
                    if (
                        "issue_id" in st.session_state
                        and "last_step_id" in st.session_state
                    ):
                        step_type = "diagnose"
                        full_response = diagnose_issue(
                            st.session_state.issue_id,
                            Request(
                                results=prompt,
                                last_step_id=st.session_state.last_step_id,
                            ),
                        )
                    else:
                        full_response = create_issue(Request(issue=prompt))

                logger.info(
                    "the %s issue response: %s - %s",
                    step_type,
                    full_response.issue_id,
                    full_response.step_id,
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                if isinstance(full_response, Response):
                    st.markdown(full_response.plan)
                    st.markdown(full_response.reasoning)
                    st.session_state.issue_id = full_response.issue_id
                    st.session_state.last_step_id = full_response.step_id
                else:
                    logging.info("the assistant should response a Response type")
                    st.write(full_response)

        except Exception as e:
            st.error(e, icon="🚨")


hidden_default_menu()
history_message()
interact()
