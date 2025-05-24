# coding: utf-8

"""
Users API
"""

from fastapi import APIRouter, Depends
from server.dependencies.services import get_db_service
from server.services.db import DatabaseService
from server.schemas.user import Request, Response

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_user(req: Request, storage_svc: DatabaseService = Depends(get_db_service)) -> Response:
    user = storage_svc.find_user(req.name)
    if user is None:
        user = storage_svc.create_user(req.name)
    return Response(id=str(user.id), name=user.name)
