from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.transcript import format_seconds_to_timestamp


class SourceCitation(BaseModel):
    chunk_id: uuid.UUID
    speaker: str
    text: str
    start_time: float
    end_time: float
    formatted_timestamp: str


class AskMeetingRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Question about the meeting")
    session_id: Optional[uuid.UUID] = Field(None, description="Optional existing chat session ID")


class AskMeetingResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    session_id: uuid.UUID
    message_id: uuid.UUID


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: List[Dict[str, Any]] = []
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    messages: List[ChatMessageResponse] = []
