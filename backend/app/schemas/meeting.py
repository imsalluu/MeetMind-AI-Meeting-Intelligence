from datetime import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.meeting import MeetingStatus, ProcessingStage


class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Meeting title")
    description: Optional[str] = Field(None, max_length=2000, description="Optional meeting notes/description")


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class MeetingStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    processing_stage: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    audio_path: Optional[str] = None
    audio_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    status: str
    processing_stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MeetingListResponse(BaseModel):
    items: List[MeetingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
