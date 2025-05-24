from pydantic import BaseModel

class HistoryRecord(BaseModel):
    role: str
    message: str
