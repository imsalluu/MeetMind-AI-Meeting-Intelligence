from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.meeting import MeetingResponse


class TopicCount(BaseModel):
    topic: str
    count: int


class StatusCount(BaseModel):
    status: str
    count: int


class AnalyticsOverviewResponse(BaseModel):
    total_meetings: int
    total_duration_hours: float
    avg_meeting_duration_minutes: float
    total_action_items: int
    pending_action_items: int
    completed_action_items: int
    action_item_completion_rate: float
    total_decisions: int
    total_topics: int
    status_distribution: List[StatusCount]
    top_topics: List[TopicCount]
    recent_meetings: List[MeetingResponse]
