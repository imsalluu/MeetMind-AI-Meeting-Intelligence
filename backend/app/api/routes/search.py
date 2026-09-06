import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting import Meeting
from app.models.meeting_topic import MeetingTopic
from app.models.transcript import TranscriptSegment
from app.models.user import User
from app.schemas.search import SearchResponse, SearchResultItem

router = APIRouter(prefix="/meetings", tags=["Search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Global search across meetings, transcripts, action items, and decisions",
)
async def search_meetings(
    q: str = Query(..., min_length=1, description="Search keyword or phrase"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    query_text = q.strip()
    term = f"%{query_text}%"
    results: list[SearchResultItem] = []

    # 1. Fetch user's meeting ids map
    meetings_q = await db.execute(
        select(Meeting.id, Meeting.title).where(Meeting.user_id == current_user.id)
    )
    user_meetings = dict(meetings_q.all())
    meeting_ids = list(user_meetings.keys())

    if not meeting_ids:
        return SearchResponse(query=query_text, results=[], total_matches=0)

    # 2. Search Meeting Titles / Descriptions
    title_matches = await db.execute(
        select(Meeting).where(
            Meeting.user_id == current_user.id,
            Meeting.title.ilike(term) | Meeting.description.ilike(term),
        )
    )
    for m in title_matches.scalars().all():
        snippet = m.description if m.description and query_text.lower() in m.description.lower() else m.title
        results.append(
            SearchResultItem(
                meeting_id=m.id,
                meeting_title=m.title,
                match_type="title",
                snippet=snippet[:200],
            )
        )

    # 3. Search Transcript Segments
    transcript_q = await db.execute(
        select(TranscriptSegment)
        .where(
            TranscriptSegment.meeting_id.in_(meeting_ids),
            TranscriptSegment.text.ilike(term),
        )
        .limit(20)
    )
    for seg in transcript_q.scalars().all():
        results.append(
            SearchResultItem(
                meeting_id=seg.meeting_id,
                meeting_title=user_meetings.get(seg.meeting_id, "Meeting"),
                match_type="transcript",
                snippet=f"{seg.speaker}: {seg.text}",
                timestamp=seg.start_time,
            )
        )

    # 4. Search Action Items
    actions_q = await db.execute(
        select(ActionItem).where(
            ActionItem.meeting_id.in_(meeting_ids),
            ActionItem.task.ilike(term) | ActionItem.assignee.ilike(term),
        )
    )
    for action in actions_q.scalars().all():
        results.append(
            SearchResultItem(
                meeting_id=action.meeting_id,
                meeting_title=user_meetings.get(action.meeting_id, "Meeting"),
                match_type="action_item",
                snippet=f"Action: {action.task} (Assignee: {action.assignee}, Due: {action.deadline})",
                timestamp=action.source_timestamp,
            )
        )

    # 5. Search Decisions
    decisions_q = await db.execute(
        select(Decision).where(
            Decision.meeting_id.in_(meeting_ids),
            Decision.decision.ilike(term),
        )
    )
    for dec in decisions_q.scalars().all():
        results.append(
            SearchResultItem(
                meeting_id=dec.meeting_id,
                meeting_title=user_meetings.get(dec.meeting_id, "Meeting"),
                match_type="decision",
                snippet=f"Decision: {dec.decision}",
                timestamp=dec.source_timestamp,
            )
        )

    # 6. Search Topics
    topics_q = await db.execute(
        select(MeetingTopic).where(
            MeetingTopic.meeting_id.in_(meeting_ids),
            MeetingTopic.topic.ilike(term) | MeetingTopic.summary.ilike(term),
        )
    )
    for top in topics_q.scalars().all():
        results.append(
            SearchResultItem(
                meeting_id=top.meeting_id,
                meeting_title=user_meetings.get(top.meeting_id, "Meeting"),
                match_type="topic",
                snippet=f"Topic: {top.topic} — {top.summary or ''}",
            )
        )

    return SearchResponse(
        query=query_text,
        results=results,
        total_matches=len(results),
    )
