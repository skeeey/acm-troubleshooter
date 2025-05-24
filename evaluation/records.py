# coding: utf-8

# pylint: disable=wrong-import-position

"""
Review the issue records
"""

import os
import sys
import uuid
import streamlit as st
from dotenv import load_dotenv
from st_aggrid import AgGrid
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server.services.db import DatabaseService

# load envs
load_dotenv()

class ResponseRecord(BaseModel):
    id: str
    created_at: str
    evaluation: str
    feedback: str

class IssueRecord(BaseModel):
    id: str
    name: str
    created_at: str
    responses: list[ResponseRecord]

def get_records() -> dict[str, IssueRecord]:
    db_svc = DatabaseService(db_url=os.getenv("DATABASE_URL"))
    records = {}
    for r in db_svc.get_issues_records():
        if r.response_id is None:
            print(f"issue {r.issue_id} does not have response")
            continue

        evaluation = "-"
        feedback = "-"

        if r.evaluation_score == 1:
            evaluation = "pos"
        elif r.evaluation_score == -1:
            evaluation = "neg"

        if r.evaluation_feedback is not None:
            feedback = r.evaluation_feedback

        resp = ResponseRecord(id=str(r.response_id), created_at=r.response_create_at.strftime("%Y-%m-%d %H:%M:%S"),
                              evaluation=evaluation, feedback=feedback)
        if r.issue_id in records:
            records[r.issue_id].responses.append(resp)
        else:
            issue_record = IssueRecord(
                id=str(r.issue_id),
                name=r.issue_name,
                created_at=r.issue_create_at.strftime("%Y-%m-%d %H:%M:%S"),
                responses=[],
            )
            issue_record.responses.append(resp)
            records[r.issue_id] = issue_record
    return records

def show_resp(resp_id: str):
    db_svc = DatabaseService(db_url=os.getenv("DATABASE_URL"))
    resp = db_svc.get_resp(uuid.UUID(resp_id))
    md = []
    if resp.user_query is not None:
        md.append("##### Query")
        md.append(resp.user_query)

    if len(resp.reasoning.strip()) != 0:
        md.append("##### Reasoning")
        md.append(resp.reasoning)

    md.append("##### Response")
    md.append(resp.asst_resp)

    if len(resp.referenced_docs) != 0:
        md.append("##### References")
        md.append("\n".join(resp.referenced_docs))

    st.markdown("\n".join(md))

if "records" not in st.session_state:
    st.session_state.records = get_records()

data = []
for key, val in st.session_state.records.items():
    data.append({"id": str(key), "issue": val.name, "created_at": val.created_at})

st.markdown("### Issues:")

r1 = AgGrid(
    None,
    gridOptions={
        "masterDetail": True,
        "rowSelection": "single",
        "suppressRowClickSelection": True,
        "pagination": True,
        "paginationAutoPageSize": True,
        "columnDefs": [
            {"field": "id", "hide": True},
            {"field": "issue", "checkboxSelection": True},
            {"field": "created_at"},
        ],
        "defaultColDef": {"flex": 1},
        "rowData": data,
    },
    allow_unsafe_jscode=True,
    key="issues",
)

if r1.selected_rows is not None:
    issue_id=r1.selected_rows.iloc[0].get("id")
    responses = []
    for rr in st.session_state.records[uuid.UUID(issue_id)].responses:
        responses.append({"response_id": rr.id, "evaluation": rr.evaluation,
                          "feedback": rr.feedback, "created_at": rr.created_at})

    st.markdown(f"##### Issue ({issue_id}) responses:")

    r2 = AgGrid(
        None,
        gridOptions={
            "masterDetail": True,
            "rowSelection": "single",
            "suppressRowClickSelection": True,
            "pagination": True,
            "paginationAutoPageSize": True,
            "columnDefs": [
                {"field": "response_id", "checkboxSelection": True},
                {"field": "evaluation"},
                {"field": "feedback"},
                {"field": "created_at"},
            ],
            "defaultColDef": {"flex": 1},
            "rowData": responses,
        },
        allow_unsafe_jscode=True,
        key="responses",
    )

    if r2.selected_rows is not None:
        rid = r2.selected_rows.iloc[0].get("response_id")
        with st.spinner(f"query response {rid}"):
            show_resp(rid)
