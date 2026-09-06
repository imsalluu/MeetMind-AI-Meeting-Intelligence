import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.models.user import User
from app.schemas.transcript import (
    MeetingTranscriptResponse,
    TranscriptSegmentResponse,
    format_seconds_to_timestamp,
)
from app.services.meeting.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["Transcription"])


@router.get(
    "/{meeting_id}/transcript",
    response_model=MeetingTranscriptResponse,
    status_code=status.HTTP_200_OK,
    summary="Get meeting transcript segments",
)
async def get_meeting_transcript(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingTranscriptResponse:
    # Ensure meeting exists and belongs to user
    meeting = await MeetingService.get_meeting(db, meeting_id, current_user.id)

    query = await db.execute(
        select(TranscriptSegment)
        .where(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.segment_order.asc(), TranscriptSegment.start_time.asc())
    )
    segments = query.scalars().all()

    segment_responses = [TranscriptSegmentResponse.model_validate(s) for s in segments]
    formatted_duration = (
        format_seconds_to_timestamp(meeting.duration_seconds)
        if meeting.duration_seconds is not None
        else None
    )

    return MeetingTranscriptResponse(
        meeting_id=meeting_id,
        segments=segment_responses,
        total_segments=len(segment_responses),
        duration_seconds=meeting.duration_seconds,
        formatted_duration=formatted_duration,
    )
