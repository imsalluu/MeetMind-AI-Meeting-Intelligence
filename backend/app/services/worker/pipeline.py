import asyncio
import time
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.db.session import async_session_factory
from app.models.meeting import Meeting, MeetingStatus, ProcessingStage
from app.services.worker.task_manager import BackgroundTaskManager


class MeetingProcessingPipeline:
    """Orchestrates end-to-end background processing for meeting audio."""

    @classmethod
    async def run(cls, meeting_id: uuid.UUID):
        """Execute all processing stages for a meeting."""
        start_time = time.time()
        logger.info(f"Starting processing pipeline for meeting_id={meeting_id}")

        async with async_session_factory() as db:
            query = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
            meeting = query.scalar_one_or_none()
            if not meeting:
                logger.error(f"Meeting {meeting_id} not found for processing")
                return

            if not meeting.audio_path:
                logger.warning(f"Meeting {meeting_id} has no audio file. Aborting pipeline.")
                await BackgroundTaskManager.update_meeting_stage(
                    db, meeting_id, MeetingStatus.FAILED, ProcessingStage.ERROR, "No audio file uploaded."
                )
                await db.commit()
                return

            try:
                # Stage 1: Status -> PROCESSING, Stage -> TRANSCRIBING
                await BackgroundTaskManager.update_meeting_stage(
                    db, meeting_id, MeetingStatus.PROCESSING, ProcessingStage.TRANSCRIBING
                )
                await db.commit()

                # Execute Transcription
                from app.services.ai.transcription import transcription_service
                stage_start = time.time()
                segments, duration = await transcription_service.transcribe_meeting(db, meeting)
                await db.commit()
                logger.info(
                    f"Stage TRANSCRIBING completed for meeting {meeting_id} in {round(time.time() - stage_start, 2)}s ({len(segments)} segments)"
                )

                # Stage 2: Stage -> ANALYZING
                await BackgroundTaskManager.update_meeting_stage(
                    db, meeting_id, MeetingStatus.PROCESSING, ProcessingStage.ANALYZING
                )
                await db.commit()

                # Execute Meeting Intelligence Extraction
                from app.services.ai.meeting_analyzer import meeting_analyzer_service
                stage_start = time.time()
                await meeting_analyzer_service.analyze_meeting(db, meeting, segments)
                await db.commit()
                logger.info(
                    f"Stage ANALYZING completed for meeting {meeting_id} in {round(time.time() - stage_start, 2)}s"
                )

                # Stage 3: Stage -> INDEXING
                await BackgroundTaskManager.update_meeting_stage(
                    db, meeting_id, MeetingStatus.PROCESSING, ProcessingStage.INDEXING
                )
                await db.commit()

                # Execute Chunking and Vector Embeddings
                from app.services.retrieval.rag import rag_service
                stage_start = time.time()
                chunks = await rag_service.index_meeting_transcript(db, meeting, segments)
                await db.commit()
                logger.info(
                    f"Stage INDEXING completed for meeting {meeting_id} in {round(time.time() - stage_start, 2)}s ({len(chunks)} chunks)"
                )

                # Stage 4: Completed & Ready
                await BackgroundTaskManager.update_meeting_stage(
                    db, meeting_id, MeetingStatus.COMPLETED, ProcessingStage.READY
                )
                await db.commit()
                total_duration = round(time.time() - start_time, 2)
                logger.info(f"Pipeline SUCCESS for meeting_id={meeting_id} in {total_duration}s")

            except Exception as e:
                total_duration = round(time.time() - start_time, 2)
                logger.exception(
                    f"Pipeline FAILED for meeting_id={meeting_id} after {total_duration}s: {e}"
                )
                await BackgroundTaskManager.update_meeting_stage(
                    db, meeting_id, MeetingStatus.FAILED, ProcessingStage.ERROR, str(e)
                )
                await db.commit()
                raise e


def trigger_meeting_processing(meeting_id: uuid.UUID):
    """Trigger background pipeline for a meeting."""
    return BackgroundTaskManager.spawn_job(
        meeting_id=meeting_id,
        job_fn=MeetingProcessingPipeline.run,
        job_name="MeetingProcessingPipeline",
    )
