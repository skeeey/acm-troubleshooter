import sys
import os
import logging
import requests

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server.models import Request, Response

# log settings
LOG_DATE_FORMAT = "%H:%M:%S"
LOG_FORMAT = "%(asctime)s - [%(levelname)s] %(module)s/%(lineno)d: %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# server settings
server_url = "http://127.0.0.1:8000"

def create_issue(req: Request)-> Response:
    print(req.model_dump_json())
    resp = requests.put(f"{server_url}/issues", data=req.model_dump_json())
    if resp.status_code == 200:
        return Response.model_validate_json(resp.content)
    
    #TODO handle errors
    logger.error("failed to create issue (status_code=%d)", resp.status_code)
    return None

def diagnose_issue(issue_id: str, req: Request)-> Response:
    resp = requests.post(f"{server_url}/issues/{issue_id}", data=req.model_dump_json())
    if resp.status_code == 200:
        return Response.model_validate_json(resp.content)
    
    #TODO handle errors
    logger.error("failed to diagnose issue (status_code=%d)", resp.status_code)
    return None

st.set_page_config(page_icon="💬", layout="wide", page_title="ACM")

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
            full_response = message["content"]
            st.markdown("##### Reasoning")
            st.markdown(full_response.reasoning)
            st.markdown("##### Plan")
            st.markdown(full_response.plan)
            hub_command = False
            spoke_command = False
            if (
                full_response.hub_commands is not None
                and len(full_response.hub_commands) > 0
            ):
                hub_command = True
            if (
                full_response.spoke_commands is not None
                and len(full_response.spoke_commands) > 0
            ):
                spoke_command = True

            if hub_command or spoke_command:
                st.markdown("##### Commands ")
            if hub_command:
                st.markdown("- hub cluster")
                st.code("\n".join(full_response.hub_commands), language="shell")
            if spoke_command:
                st.markdown("- spoke cluster")
                st.code("\n".join(full_response.spoke_commands), language="shell")
        else:
            st.markdown(message["content"])


def interact():
    if prompt := st.chat_input("Put the ACM issue here..."):
        if "/clear" == str.strip(prompt).lower():
            logger.info("clean the current session")
            st.session_state.clear()
            return

        with st.chat_message("user", avatar="👨‍💻"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            # Use the generator function with st.write_stream
            with st.chat_message("assistant", avatar="🤖"):

                with st.spinner("Processing"):
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

                # import rich
                # rich.print(full_response)
                if isinstance(full_response, Response):
                    st.markdown("##### Reasoning")
                    st.markdown(full_response.reasoning)
                    st.markdown("##### Plan")
                    st.markdown(full_response.plan)
                    hub_command = False
                    spoke_command = False
                    if (
                        full_response.hub_commands is not None
                        and len(full_response.hub_commands) > 0
                    ):
                        hub_command = True
                    if (
                        full_response.spoke_commands is not None
                        and len(full_response.spoke_commands) > 0
                    ):
                        spoke_command = True

                    if hub_command == True or spoke_command == True:
                        st.markdown("##### Commands ")

                    if hub_command == True:
                        st.markdown("- hub cluster")
                        st.code("\n".join(full_response.hub_commands), language="shell")
                    if spoke_command == True:
                        st.markdown("- spoke cluster")
                        st.code(
                            "\n".join(full_response.spoke_commands), language="shell"
                        )
                    # st.markdown(full_response.plan)
                    # st.markdown(full_response.reasoning)
                    st.session_state.issue_id = full_response.issue_id
                    st.session_state.last_step_id = full_response.step_id
                else:
                    logging.info("the assistant should response a Response type")
                    st.write(full_response)

                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
        except Exception as e:
            st.error(e, icon="🚨")


interact()
