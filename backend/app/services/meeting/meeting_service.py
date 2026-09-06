import math
import os
import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import AppException, EntityNotFoundException, ForbiddenException, ValidationException
from app.core.logging import logger
from app.models.meeting import Meeting, MeetingStatus, ProcessingStage
from app.schemas.meeting import MeetingCreate, MeetingListResponse, MeetingResponse, MeetingStatusResponse, MeetingUpdate
from app.services.storage.local_storage import storage_service


class MeetingService:
    """Service handling meeting CRUD, audio validation, and audio storage."""

    @staticmethod
    async def create_meeting(
        db: AsyncSession,
        user_id: uuid.UUID,
        data: MeetingCreate,
    ) -> Meeting:
        meeting = Meeting(
            user_id=user_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            status=MeetingStatus.PENDING.value,
            processing_stage=ProcessingStage.UPLOADING.value,
        )
        db.add(meeting)
        await db.flush()
        await db.refresh(meeting)
        logger.info(f"Created meeting {meeting.id} for user {user_id}")
        return meeting

    @staticmethod
    async def get_meeting(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Meeting:
        query = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = query.scalar_one_or_none()
        if not meeting:
            raise EntityNotFoundException("Meeting", str(meeting_id))
        if meeting.user_id != user_id:
            raise ForbiddenException("You do not have access to this meeting.")
        return meeting

    @staticmethod
    async def upload_audio(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        file: UploadFile,
    ) -> Meeting:
        meeting = await MeetingService.get_meeting(db, meeting_id, user_id)

        # 1. Validate file extension
        filename = file.filename or "recording.mp3"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
            raise ValidationException(
                f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
            )

        # 2. Read and validate file size
        content = await file.read()
        file_size = len(content)
        if file_size == 0:
            raise ValidationException("The uploaded audio file is empty.")
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValidationException(
                f"File size ({round(file_size / (1024 * 1024), 2)} MB) exceeds limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            )

        # 3. Store audio file safely under sanitized key: meetings/{user_id}/{meeting_id}/{sanitized_filename}
        storage_rel_path = f"meetings/{user_id}/{meeting_id}/{uuid.uuid4().hex}{ext}"
        saved_path = await storage_service.upload(content, storage_rel_path)

        # 4. Update meeting record
        meeting.audio_path = saved_path
        meeting.audio_filename = filename
        meeting.file_size_bytes = file_size
        meeting.status = MeetingStatus.PENDING.value
        meeting.processing_stage = ProcessingStage.UPLOADING.value
        meeting.error_message = None

        await db.flush()
        await db.refresh(meeting)
        logger.info(f"Audio uploaded for meeting {meeting_id} ({file_size} bytes)")
        return meeting

    @staticmethod
    async def list_meetings(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> MeetingListResponse:
        base_query = select(Meeting).where(Meeting.user_id == user_id)
        count_query = select(func.count(Meeting.id)).where(Meeting.user_id == user_id)

        if status_filter:
            base_query = base_query.where(Meeting.status == status_filter.upper())
            count_query = count_query.where(Meeting.status == status_filter.upper())

        if search_query:
            term = f"%{search_query.strip()}%"
            base_query = base_query.where(Meeting.title.ilike(term) | Meeting.description.ilike(term))
            count_query = count_query.where(Meeting.title.ilike(term) | Meeting.description.ilike(term))

        # Total count
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated items
        offset = (page - 1) * page_size
        items_query = await db.execute(
            base_query.order_by(Meeting.created_at.desc()).offset(offset).limit(page_size)
        )
        meetings = items_query.scalars().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return MeetingListResponse(
            items=[MeetingResponse.model_validate(m) for m in meetings],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def update_meeting(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MeetingUpdate,
    ) -> Meeting:
        meeting = await MeetingService.get_meeting(db, meeting_id, user_id)
        if data.title is not None:
            meeting.title = data.title.strip()
        if data.description is not None:
            meeting.description = data.description.strip()
        await db.flush()
        await db.refresh(meeting)
        return meeting

    @staticmethod
    async def delete_meeting(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        meeting = await MeetingService.get_meeting(db, meeting_id, user_id)
        
        # Delete audio file from storage if present
        if meeting.audio_path:
            await storage_service.delete(meeting.audio_path)

        await db.delete(meeting)
        await db.flush()
        logger.info(f"Deleted meeting {meeting_id} for user {user_id}")
        return True

    @staticmethod
    async def get_status(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MeetingStatusResponse:
        meeting = await MeetingService.get_meeting(db, meeting_id, user_id)
        return MeetingStatusResponse.model_validate(meeting)
