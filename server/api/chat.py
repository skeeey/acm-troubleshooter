# coding: utf-8

"""
Chats API
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from server.dependencies.services import get_db_service, get_workflow_service
from server.models.workflow import HistoryRecord
from server.schemas.chat import Request, Response
from server.services.db import DatabaseService
from server.services.workflow import WorkflowService
from server.tools.common import is_empty

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(req: Request,
               db_svc: DatabaseService = Depends(get_db_service),
               workflow_svc: WorkflowService = Depends(get_workflow_service)) -> Response:
    if is_empty(req.query):
        raise HTTPException(status_code=422, detail="the user inputs are required")
    
    docs = db_svc.list_document_views()
    if len(docs) == 0:
        raise HTTPException(status_code=500, detail="there are no docs")

    issue_id = req.issue_id
    histories = []

    if is_empty(issue_id):
        issue = db_svc.create_issue(user_id=uuid.UUID(req.user_id), name=req.query)
    else:
        issue = db_svc.get_issue(uuid.UUID(issue_id))
        if issue is None:
            raise HTTPException(status_code=404, detail="the issue not found")
        for resp in db_svc.list_resp(issue_id=issue.id):
            histories.append(HistoryRecord(role="user", message=resp.user_query))
            histories.append(HistoryRecord(role="assistant", message=resp.asst_resp))

    try:
        llm_resp = workflow_svc.run(query=req.query, histories=histories, docs=docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to get response from llm, {e}") from e

    db_resp = db_svc.create_resp(
        issue_id=issue.id,
        user_query=req.query,
        asst_resp=llm_resp["response"],
        reasoning=llm_resp["reasoning"],
        referenced_docs = llm_resp["relevant_doc_names"],
    )

    return Response(
        issue_id=str(db_resp.issue_id),
        resp_id=str(db_resp.id),
        resp=db_resp.asst_resp,
        reasoning=db_resp.reasoning,
        references="\n".join(f"- {item}" for item in llm_resp["relevant_doc_names"]))
