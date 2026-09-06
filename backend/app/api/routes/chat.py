import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import AskMeetingRequest, AskMeetingResponse, ChatSessionResponse
from app.services.ai.chat_service import chat_service

router = APIRouter(prefix="/meetings", tags=["Ask This Meeting"])


@router.post(
    "/{meeting_id}/ask",
    response_model=AskMeetingResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about the meeting (Transcript-grounded RAG)",
)
async def ask_meeting(
    meeting_id: uuid.UUID,
    request: AskMeetingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AskMeetingResponse:
    return await chat_service.ask_meeting(
        db=db,
        user_id=current_user.id,
        meeting_id=meeting_id,
        request=request,
    )


@router.get(
    "/{meeting_id}/chat/sessions",
    response_model=List[ChatSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List chat sessions for a meeting",
)
async def list_chat_sessions(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatSessionResponse]:
    sessions = await chat_service.list_sessions(db, current_user.id, meeting_id)
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get(
    "/{meeting_id}/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session with messages and sources",
)
async def get_chat_session(
    meeting_id: uuid.UUID,
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    session = await chat_service.get_session(db, current_user.id, meeting_id, session_id)
    return ChatSessionResponse.model_validate(session)
