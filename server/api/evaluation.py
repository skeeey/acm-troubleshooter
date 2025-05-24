
# coding: utf-8

"""
Evaluation API
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from server.dependencies.services import get_db_service
from server.services.db import DatabaseService
from server.schemas.evaluation import Request

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.put("/")
async def evaluate(req: Request, db_svc: DatabaseService = Depends(get_db_service)):
    issue = db_svc.get_issue(uuid.UUID(req.issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")

    resp = db_svc.get_resp(uuid.UUID(req.resp_id))
    if resp is None:
        raise HTTPException(status_code=404, detail="the responses not found")

    db_svc.evaluate(issue.id, resp.id, req.score, req.feedback)
