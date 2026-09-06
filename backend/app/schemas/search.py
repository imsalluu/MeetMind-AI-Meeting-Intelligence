import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.transcript import format_seconds_to_timestamp


class SearchResultItem(BaseModel):
    meeting_id: uuid.UUID
    meeting_title: str
    match_type: str  # "transcript" | "action_item" | "decision" | "topic" | "title"
    snippet: str
    timestamp: Optional[float] = None
    
    @property
    def formatted_timestamp(self) -> Optional[str]:
        return format_seconds_to_timestamp(self.timestamp) if self.timestamp is not None else None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_matches: int
