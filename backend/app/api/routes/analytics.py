from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_topic import MeetingTopic
from app.models.user import User
from app.schemas.analytics import AnalyticsOverviewResponse, StatusCount, TopicCount
from app.schemas.meeting import MeetingResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user meeting intelligence analytics overview",
)
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewResponse:
    # 1. User meetings
    meetings_query = await db.execute(
        select(Meeting)
        .where(Meeting.user_id == current_user.id)
        .order_by(Meeting.created_at.desc())
    )
    user_meetings = list(meetings_query.scalars().all())
    total_meetings = len(user_meetings)

    # 2. Total duration and averages
    total_seconds = sum((m.duration_seconds or 0.0) for m in user_meetings)
    total_duration_hours = round(total_seconds / 3600.0, 2)
    avg_duration_minutes = (
        round((total_seconds / total_meetings) / 60.0, 1) if total_meetings > 0 else 0.0
    )

    # 3. Status distribution
    status_counts_map: dict[str, int] = {}
    for m in user_meetings:
        status_counts_map[m.status] = status_counts_map.get(m.status, 0) + 1

    status_distribution = [
        StatusCount(status=st, count=cnt) for st, cnt in status_counts_map.items()
    ]

    # 4. Action items aggregated across user meetings
    meeting_ids = [m.id for m in user_meetings]
    if meeting_ids:
        actions_query = await db.execute(
            select(ActionItem).where(ActionItem.meeting_id.in_(meeting_ids))
        )
        all_actions = list(actions_query.scalars().all())
        total_actions = len(all_actions)
        completed_actions = sum(1 for a in all_actions if a.is_completed)
        pending_actions = total_actions - completed_actions
        completion_rate = (
            round((completed_actions / total_actions) * 100, 1) if total_actions > 0 else 0.0
        )

        # 5. Decisions
        decisions_query = await db.execute(
            select(func.count(Decision.id)).where(Decision.meeting_id.in_(meeting_ids))
        )
        total_decisions = decisions_query.scalar_one()

        # 6. Topics & Top Topics
        topics_query = await db.execute(
            select(MeetingTopic.topic, func.count(MeetingTopic.id))
            .where(MeetingTopic.meeting_id.in_(meeting_ids))
            .group_by(MeetingTopic.topic)
            .order_by(func.count(MeetingTopic.id).desc())
            .limit(8)
        )
        top_topics_rows = topics_query.all()
        top_topics = [TopicCount(topic=row[0], count=row[1]) for row in top_topics_rows]
        total_topics = sum(t.count for t in top_topics)

    else:
        total_actions = 0
        completed_actions = 0
        pending_actions = 0
        completion_rate = 0.0
        total_decisions = 0
        total_topics = 0
        top_topics = []

    # 7. Recent meetings (up to 5)
    recent_meetings = [
        MeetingResponse.model_validate(m) for m in user_meetings[:5]
    ]

    return AnalyticsOverviewResponse(
        total_meetings=total_meetings,
        total_duration_hours=total_duration_hours,
        avg_meeting_duration_minutes=avg_duration_minutes,
        total_action_items=total_actions,
        pending_action_items=pending_actions,
        completed_action_items=completed_actions,
        action_item_completion_rate=completion_rate,
        total_decisions=total_decisions,
        total_topics=total_topics,
        status_distribution=status_distribution,
        top_topics=top_topics,
        recent_meetings=recent_meetings,
    )
