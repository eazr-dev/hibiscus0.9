"""
MongoDB-specific Pydantic models
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class MongoDBChatHistoryRequest(BaseModel):
    session_id: str
    user_id: int
    limit: Optional[int] = 20


class MongoDBSearchChatRequest(BaseModel):
    session_id: str
    user_id: int
    query: str
    limit: Optional[int] = 10


class MongoDBClearChatRequest(BaseModel):
    session_id: str
    user_id: int
    confirm: bool = False


class MongoDBUpdateUserProfileRequest(BaseModel):
    session_id: str
    user_id: int
    profile_data: Dict[str, Any]


class MongoDBUserStatsRequest(BaseModel):
    user_id: int
