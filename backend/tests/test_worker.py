import asyncio
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting import Meeting, MeetingStatus, ProcessingStage
from app.models.user import User
from app.services.worker.task_manager import BackgroundTaskManager


@pytest.mark.asyncio
async def test_background_task_manager_lifecycle(db_session: AsyncSession):
    # 1. Create User and Meeting
    user = User(email="worker.test@meetmind.ai", hashed_password="pw", full_name="Worker Tester")
    db_session.add(user)
    await db_session.flush()

    meeting = Meeting(
        user_id=user.id,
        title="Background Job Test Meeting",
        status=MeetingStatus.PENDING.value,
        processing_stage=ProcessingStage.UPLOADING.value,
    )
    db_session.add(meeting)
    await db_session.flush()

    # 2. Test transition to PROCESSING / TRANSCRIBING
    await BackgroundTaskManager.update_meeting_stage(
        db_session, meeting.id, MeetingStatus.PROCESSING, ProcessingStage.TRANSCRIBING
    )
    await db_session.refresh(meeting)
    assert meeting.status == MeetingStatus.PROCESSING.value
    assert meeting.processing_stage == ProcessingStage.TRANSCRIBING.value

    # 3. Test transition to PROCESSING / ANALYZING
    await BackgroundTaskManager.update_meeting_stage(
        db_session, meeting.id, MeetingStatus.PROCESSING, ProcessingStage.ANALYZING
    )
    await db_session.refresh(meeting)
    assert meeting.processing_stage == ProcessingStage.ANALYZING.value

    # 4. Test transition to COMPLETED / READY
    await BackgroundTaskManager.update_meeting_stage(
        db_session, meeting.id, MeetingStatus.COMPLETED, ProcessingStage.READY
    )
    await db_session.refresh(meeting)
    assert meeting.status == MeetingStatus.COMPLETED.value
    assert meeting.processing_stage == ProcessingStage.READY.value

    # 5. Test transition to FAILED / ERROR with error message
    await BackgroundTaskManager.update_meeting_stage(
        db_session, meeting.id, MeetingStatus.FAILED, ProcessingStage.ERROR, "OpenAI API timeout"
    )
    await db_session.refresh(meeting)
    assert meeting.status == MeetingStatus.FAILED.value
    assert meeting.processing_stage == ProcessingStage.ERROR.value
    assert meeting.error_message == "OpenAI API timeout"
