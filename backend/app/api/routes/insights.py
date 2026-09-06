import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.exceptions import EntityNotFoundException
from app.db.session import get_db
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting_insight import MeetingInsight
from app.models.meeting_topic import MeetingTopic
from app.models.user import User
from app.schemas.intelligence import (
    ActionItemResponse,
    DecisionResponse,
    MeetingInsightsOverviewResponse,
    MeetingSummaryResponse,
    TopicResponse,
)
from app.services.meeting.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["Meeting Intelligence"])


class ActionItemToggle(BaseModel):
    is_completed: bool


@router.get(
    "/{meeting_id}/summary",
    response_model=MeetingSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get meeting summaries and key points",
)
async def get_meeting_summary(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingSummaryResponse:
    await MeetingService.get_meeting(db, meeting_id, current_user.id)
    query = await db.execute(
        select(MeetingInsight).where(MeetingInsight.meeting_id == meeting_id)
    )
    insight = query.scalar_one_or_none()
    if not insight:
        return MeetingSummaryResponse(meeting_id=meeting_id)
    return MeetingSummaryResponse.model_validate(insight)


@router.get(
    "/{meeting_id}/actions",
    response_model=List[ActionItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get meeting action items",
)
async def get_meeting_action_items(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ActionItemResponse]:
    await MeetingService.get_meeting(db, meeting_id, current_user.id)
    query = await db.execute(
        select(ActionItem)
        .where(ActionItem.meeting_id == meeting_id)
        .order_by(ActionItem.source_timestamp.asc().nulls_last())
    )
    items = query.scalars().all()
    return [ActionItemResponse.model_validate(i) for i in items]


@router.patch(
    "/{meeting_id}/actions/{action_id}",
    response_model=ActionItemResponse,
    summary="Toggle action item completion status",
)
async def toggle_action_item(
    meeting_id: uuid.UUID,
    action_id: uuid.UUID,
    data: ActionItemToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActionItemResponse:
    await MeetingService.get_meeting(db, meeting_id, current_user.id)
    query = await db.execute(
        select(ActionItem).where(
            ActionItem.id == action_id, ActionItem.meeting_id == meeting_id
        )
    )
    action = query.scalar_one_or_none()
    if not action:
        raise EntityNotFoundException("ActionItem", str(action_id))

    action.is_completed = data.is_completed
    await db.flush()
    await db.refresh(action)
    return ActionItemResponse.model_validate(action)


@router.get(
    "/{meeting_id}/decisions",
    response_model=List[DecisionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get meeting decisions",
)
async def get_meeting_decisions(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[DecisionResponse]:
    await MeetingService.get_meeting(db, meeting_id, current_user.id)
    query = await db.execute(
        select(Decision)
        .where(Decision.meeting_id == meeting_id)
        .order_by(Decision.source_timestamp.asc().nulls_last())
    )
    decisions = query.scalars().all()
    return [DecisionResponse.model_validate(d) for d in decisions]


@router.get(
    "/{meeting_id}/topics",
    response_model=List[TopicResponse],
    status_code=status.HTTP_200_OK,
    summary="Get meeting topics",
)
async def get_meeting_topics(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TopicResponse]:
    await MeetingService.get_meeting(db, meeting_id, current_user.id)
    query = await db.execute(
        select(MeetingTopic)
        .where(MeetingTopic.meeting_id == meeting_id)
        .order_by(MeetingTopic.created_at.asc())
    )
    topics = query.scalars().all()
    return [TopicResponse.model_validate(t) for t in topics]


@router.get(
    "/{meeting_id}/insights",
    response_model=MeetingInsightsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete meeting insights overview",
)
async def get_meeting_insights_overview(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingInsightsOverviewResponse:
    await MeetingService.get_meeting(db, meeting_id, current_user.id)

    # 1. Summary
    insight_query = await db.execute(
        select(MeetingInsight).where(MeetingInsight.meeting_id == meeting_id)
    )
    insight = insight_query.scalar_one_or_none()
    summary_resp = (
        MeetingSummaryResponse.model_validate(insight)
        if insight
        else MeetingSummaryResponse(meeting_id=meeting_id)
    )

    # 2. Actions
    actions_query = await db.execute(
        select(ActionItem).where(ActionItem.meeting_id == meeting_id)
    )
    action_items = [ActionItemResponse.model_validate(i) for i in actions_query.scalars().all()]

    # 3. Decisions
    decisions_query = await db.execute(
        select(Decision).where(Decision.meeting_id == meeting_id)
    )
    decisions = [DecisionResponse.model_validate(d) for d in decisions_query.scalars().all()]

    # 4. Topics
    topics_query = await db.execute(
        select(MeetingTopic).where(MeetingTopic.meeting_id == meeting_id)
    )
    topics = [TopicResponse.model_validate(t) for t in topics_query.scalars().all()]

    return MeetingInsightsOverviewResponse(
        meeting_id=meeting_id,
        summary=summary_resp,
        action_items=action_items,
        decisions=decisions,
        topics=topics,
    )
