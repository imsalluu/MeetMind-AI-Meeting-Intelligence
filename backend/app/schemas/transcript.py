from datetime import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, computed_field


def format_seconds_to_timestamp(seconds: float) -> str:
    """Format float seconds to MM:SS or HH:MM:SS string."""
    if seconds is None:
        return "00:00"
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class TranscriptSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None
    segment_order: int

    @computed_field
    def formatted_start(self) -> str:
        return format_seconds_to_timestamp(self.start_time)

    @computed_field
    def formatted_end(self) -> str:
        return format_seconds_to_timestamp(self.end_time)


class MeetingTranscriptResponse(BaseModel):
    meeting_id: uuid.UUID
    segments: List[TranscriptSegmentResponse]
    total_segments: int
    duration_seconds: Optional[float] = None
    formatted_duration: Optional[str] = None
