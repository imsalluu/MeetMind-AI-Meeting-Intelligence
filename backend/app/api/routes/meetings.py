import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingStatusResponse,
    MeetingUpdate,
)
from app.services.meeting.meeting_service import MeetingService
from app.services.storage.local_storage import storage_service

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED, summary="Create meeting record")
async def create_meeting(
    data: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    meeting = await MeetingService.create_meeting(db, current_user.id, data)
    return MeetingResponse.model_validate(meeting)


@router.post("/{meeting_id}/upload", response_model=MeetingResponse, summary="Upload audio recording")
async def upload_audio(
    meeting_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    meeting = await MeetingService.upload_audio(db, meeting_id, current_user.id, file)
    return MeetingResponse.model_validate(meeting)


@router.get("", response_model=MeetingListResponse, summary="List user meetings")
async def list_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: PENDING, PROCESSING, COMPLETED, FAILED"),
    q: Optional[str] = Query(None, description="Search query for meeting title or description"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingListResponse:
    return await MeetingService.list_meetings(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status,
        search_query=q,
    )


@router.get("/{meeting_id}", response_model=MeetingResponse, summary="Get meeting details")
async def get_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    meeting = await MeetingService.get_meeting(db, meeting_id, current_user.id)
    return MeetingResponse.model_validate(meeting)


@router.patch("/{meeting_id}", response_model=MeetingResponse, summary="Update meeting details")
async def update_meeting(
    meeting_id: uuid.UUID,
    data: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    meeting = await MeetingService.update_meeting(db, meeting_id, current_user.id, data)
    return MeetingResponse.model_validate(meeting)


@router.delete("/{meeting_id}", status_code=status.HTTP_200_OK, summary="Delete meeting")
async def delete_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await MeetingService.delete_meeting(db, meeting_id, current_user.id)
    return {"message": "Meeting deleted successfully", "id": str(meeting_id)}


@router.get("/{meeting_id}/status", response_model=MeetingStatusResponse, summary="Get meeting processing status")
async def get_meeting_status(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingStatusResponse:
    return await MeetingService.get_status(db, meeting_id, current_user.id)


@router.get("/{meeting_id}/audio", summary="Stream audio recording")
async def stream_audio(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await MeetingService.get_meeting(db, meeting_id, current_user.id)
    if not meeting.audio_path:
        raise HTTPException(status_code=404, detail="No audio file uploaded for this meeting.")

    abs_path = storage_service.get_absolute_path(meeting.audio_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Audio file not found on storage.")

    # Determine content type
    ext = os.path.splitext(abs_path)[1].lower()
    media_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".mp4": "video/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=abs_path,
        media_type=media_type,
        filename=meeting.audio_filename or f"meeting_{meeting_id}{ext}",
    )
