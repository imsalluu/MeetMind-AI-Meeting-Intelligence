import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.transcript import format_seconds_to_timestamp


class ExtractedActionItem(BaseModel):
    task: str = Field(..., description="Task description")
    assignee: str = Field(default="Not specified", description="Assignee name or 'Not specified'")
    deadline: str = Field(default="Not specified", description="Deadline string or 'Not specified'")
    source_timestamp: Optional[float] = Field(None, description="Timestamp in seconds where this task was mentioned")


class ExtractedDecision(BaseModel):
    decision: str = Field(..., description="Decision summary")
    source_timestamp: Optional[float] = Field(None, description="Timestamp in seconds where this decision was agreed")


class ExtractedTopic(BaseModel):
    topic: str = Field(..., description="Topic headline")
    summary: Optional[str] = Field(None, description="Summary of topic discussion")


class MeetingIntelligenceOutput(BaseModel):
    executive_summary: str = Field(..., description="Executive level summary")
    short_summary: str = Field(..., description="Single sentence summary")
    detailed_summary: str = Field(..., description="Detailed section-by-section summary")
    key_points: List[str] = Field(default_factory=list, description="List of key points")
    action_items: List[ExtractedActionItem] = Field(default_factory=list, description="Action items")
    decisions: List[ExtractedDecision] = Field(default_factory=list, description="Decisions made")
    topics: List[ExtractedTopic] = Field(default_factory=list, description="Topics discussed")
    risks: List[str] = Field(default_factory=list, description="Identified risks or concerns")
    questions: List[str] = Field(default_factory=list, description="Open questions or follow-up items")


# --- Response Schemas for REST API ---

class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    task: str
    assignee: str
    deadline: str
    source_timestamp: Optional[float] = None
    is_completed: bool

    @property
    def formatted_timestamp(self) -> Optional[str]:
        return format_seconds_to_timestamp(self.source_timestamp) if self.source_timestamp is not None else None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    decision: str
    source_timestamp: Optional[float] = None

    @property
    def formatted_timestamp(self) -> Optional[str]:
        return format_seconds_to_timestamp(self.source_timestamp) if self.source_timestamp is not None else None


class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    topic: str
    summary: Optional[str] = None


class MeetingSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    meeting_id: uuid.UUID
    executive_summary: Optional[str] = None
    short_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    key_points: List[str] = []
    risks: List[str] = []
    questions: List[str] = []


class MeetingInsightsOverviewResponse(BaseModel):
    meeting_id: uuid.UUID
    summary: MeetingSummaryResponse
    action_items: List[ActionItemResponse]
    decisions: List[DecisionResponse]
    topics: List[TopicResponse]
