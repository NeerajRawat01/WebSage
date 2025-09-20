from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime


class QAExchangeLite(BaseModel):
    user_query: str
    agent_response: str


class QAExchangeHistory(BaseModel):
    user_query: str
    agent_response: str
    created_at: datetime


class ConverseRequest(BaseModel):
    url: Optional[HttpUrl] = None
    session_id: Optional[str] = None
    query: str
    conversation_history: Optional[List[QAExchangeLite]] = None


class ConverseResponse(BaseModel):
    url: HttpUrl
    user_query: str
    agent_response: str
    context_sources: List[str]


