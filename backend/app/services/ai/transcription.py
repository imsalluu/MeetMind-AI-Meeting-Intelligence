import os
import uuid
from typing import List, Tuple
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AIProcessingException
from app.core.logging import logger
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.services.ai.llm import ai_client_service
from app.services.storage.local_storage import storage_service


class TranscriptionService:
    """Service handling audio transcription via OpenAI Whisper API and transcript normalization."""

    @classmethod
    async def transcribe_meeting(
        cls,
        db: AsyncSession,
        meeting: Meeting,
    ) -> Tuple[List[TranscriptSegment], float]:
        if not meeting.audio_path:
            raise AIProcessingException("No audio file found for transcription.")

        abs_path = storage_service.get_absolute_path(meeting.audio_path)
        if not os.path.exists(abs_path):
            raise AIProcessingException(f"Audio file does not exist on storage: {meeting.audio_path}")

        logger.info(f"Initiating Whisper transcription for meeting {meeting.id} ({abs_path})")

        try:
            # 1. Call OpenAI Whisper API with segment timestamps
            with open(abs_path, "rb") as audio_file:
                transcript_response = await ai_client_service.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

        except Exception as e:
            logger.exception(f"OpenAI transcription API call failed for meeting {meeting.id}: {e}")
            raise AIProcessingException(f"Transcription failed: {str(e)}")

        # 2. Extract and normalize segments
        raw_segments = getattr(transcript_response, "segments", None)
        total_duration = getattr(transcript_response, "duration", None)

        created_segments: List[TranscriptSegment] = []

        # Clear any prior segments for idempotency
        await db.execute(delete(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting.id))

        if raw_segments and len(raw_segments) > 0:
            for idx, seg in enumerate(raw_segments):
                # Safe attribute/dict access
                if isinstance(seg, dict):
                    text = seg.get("text", "").strip()
                    start_t = float(seg.get("start", 0.0))
                    end_t = float(seg.get("end", start_t + 1.0))
                else:
                    text = getattr(seg, "text", "").strip()
                    start_t = float(getattr(seg, "start", 0.0))
                    end_t = float(getattr(seg, "end", start_t + 1.0))

                if not text:
                    continue

                # Production rule: Assign neutral speaker placeholder without fabricating identities
                speaker_label = "Speaker 1"

                segment = TranscriptSegment(
                    meeting_id=meeting.id,
                    speaker=speaker_label,
                    text=text,
                    start_time=round(start_t, 2),
                    end_time=round(end_t, 2),
                    confidence=1.0,
                    segment_order=idx,
                )
                db.add(segment)
                created_segments.append(segment)

            if total_duration is None and created_segments:
                total_duration = created_segments[-1].end_time

        else:
            # Fallback if no granular segments returned: use full transcript text
            full_text = getattr(transcript_response, "text", "").strip()
            if full_text:
                total_duration = total_duration or 60.0
                segment = TranscriptSegment(
                    meeting_id=meeting.id,
                    speaker="Speaker 1",
                    text=full_text,
                    start_time=0.0,
                    end_time=round(total_duration, 2),
                    confidence=1.0,
                    segment_order=0,
                )
                db.add(segment)
                created_segments.append(segment)

        # 3. Update meeting duration
        meeting.duration_seconds = round(total_duration or 0.0, 2)
        await db.flush()

        logger.info(
            f"Successfully processed {len(created_segments)} transcript segments for meeting {meeting.id} (duration={meeting.duration_seconds}s)"
        )
        return created_segments, meeting.duration_seconds


transcription_service = TranscriptionService()
