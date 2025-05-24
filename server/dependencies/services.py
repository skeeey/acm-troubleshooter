import os
from server.models.embeddings import BGE
from server.services.db import DatabaseService
from server.services.vector import VectorStoreService
from server.services.workflow import WorkflowService
from server.services.slack import SlackService

_db_svc = None
_index_svc = None
_workflow_svc = None
_slack_svc = None

async def get_db_service() -> DatabaseService:
    global _db_svc
    if _db_svc is None:
        _db_svc = DatabaseService(db_url=os.getenv("DATABASE_URL"))
    return _db_svc

async def get_vector_store_service() -> VectorStoreService:
    global _index_svc
    if _index_svc is None:
        _index_svc = VectorStoreService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
    return _index_svc

async def get_workflow_service() -> VectorStoreService:
    global _index_svc
    global _workflow_svc

    if _index_svc is None:
        _index_svc = VectorStoreService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
    
    if _workflow_svc is None:
        _workflow_svc = WorkflowService(vector_store_svc=_index_svc)
    return _workflow_svc

async def get_slack_service() -> SlackService:
    global _index_svc
    global _workflow_svc
    global _slack_svc

    if _index_svc is None:
        _index_svc = VectorStoreService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
    
    if _workflow_svc is None:
        _workflow_svc = WorkflowService(vector_store_svc=_index_svc)

    if _slack_svc is None:
        _slack_svc = SlackService(workflow_svc=_workflow_svc)
    return _slack_svc
