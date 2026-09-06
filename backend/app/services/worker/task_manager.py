import asyncio
import time
import uuid
from typing import Callable, Coroutine, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.db.session import async_session_factory
from app.models.meeting import Meeting, MeetingStatus, ProcessingStage


class BackgroundTaskManager:
    """Manages background async jobs with execution tracking, stage logging, and error handling."""

    @staticmethod
    def spawn_job(
        meeting_id: uuid.UUID,
        job_fn: Callable[[uuid.UUID], Coroutine],
        job_name: str = "meeting_processing_pipeline",
    ) -> asyncio.Task:
        """Spawn background coroutine safely and attach error callback."""
        task_id = f"job_{uuid.uuid4().hex[:8]}"
        logger.info(f"Enqueued background job [{job_name}] id={task_id} for meeting={meeting_id}")

        async def _wrapper():
            start_ts = time.time()
            try:
                await job_fn(meeting_id)
                duration = round(time.time() - start_ts, 2)
                logger.info(
                    f"Completed background job [{job_name}] id={task_id} for meeting={meeting_id} in {duration}s"
                )
            except Exception as e:
                duration = round(time.time() - start_ts, 2)
                logger.exception(
                    f"Background job [{job_name}] id={task_id} failed for meeting={meeting_id} after {duration}s: {e}"
                )
                await BackgroundTaskManager._mark_meeting_failed(meeting_id, str(e))

        task = asyncio.create_task(_wrapper())
        return task

    @staticmethod
    async def _mark_meeting_failed(meeting_id: uuid.UUID, error_msg: str):
        """Safely record failure in database using independent session."""
        try:
            async with async_session_factory() as session:
                meeting = await session.get(Meeting, meeting_id)
                if meeting:
                    meeting.status = MeetingStatus.FAILED.value
                    meeting.processing_stage = ProcessingStage.ERROR.value
                    meeting.error_message = error_msg[:1000]
                    await session.commit()
                    logger.warning(f"Recorded FAILED status for meeting {meeting_id}")
        except Exception as db_err:
            logger.error(f"Failed to record error state for meeting {meeting_id}: {db_err}")

    @staticmethod
    async def update_meeting_stage(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        status: MeetingStatus,
        stage: ProcessingStage,
        error_message: Optional[str] = None,
    ):
        """Update meeting state and stage in database."""
        meeting = await db.get(Meeting, meeting_id)
        if meeting:
            meeting.status = status.value
            meeting.processing_stage = stage.value
            if error_message is not None:
                meeting.error_message = error_message
            await db.flush()
            logger.info(
                f"Meeting {meeting_id} transitioned -> status={status.value} stage={stage.value}"
            )
