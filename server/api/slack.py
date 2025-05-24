# coding: utf-8

"""
Slack API
"""

from fastapi import APIRouter, Depends, Request
from server.dependencies.services import get_slack_service
from server.services.slack import SlackService

router = APIRouter(prefix="/slack", tags=["slack"])

@router.post("/callback")
async def endpoint(request: Request, slack_svc: SlackService = Depends(get_slack_service)):
    data = await request.json()
    if "challenge" in data:
        return {"challenge": data["challenge"]}
    return await slack_svc.handle(request)
