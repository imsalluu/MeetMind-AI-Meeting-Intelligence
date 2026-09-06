import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import AIProcessingException, EntityNotFoundException, ForbiddenException
from app.core.logging import logger
from app.models.chat import ChatMessage, ChatSession
from app.models.meeting import Meeting
from app.prompts.rag import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT_TEMPLATE
from app.schemas.chat import AskMeetingRequest, AskMeetingResponse, SourceCitation
from app.schemas.transcript import format_seconds_to_timestamp
from app.services.ai.llm import ai_client_service
from app.services.meeting.meeting_service import MeetingService
from app.services.retrieval.rag import rag_service


class ChatService:
    """Service handling transcript-grounded conversational RAG ('Ask This Meeting')."""

    @classmethod
    async def ask_meeting(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        meeting_id: uuid.UUID,
        request: AskMeetingRequest,
    ) -> AskMeetingResponse:
        # 1. Verify meeting exists and belongs to user
        meeting = await MeetingService.get_meeting(db, meeting_id, user_id)

        # 2. Get or create ChatSession
        session_id = request.session_id
        if session_id:
            query = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.meeting_id == meeting_id,
                    ChatSession.user_id == user_id,
                )
            )
            chat_session = query.scalar_one_or_none()
            if not chat_session:
                raise EntityNotFoundException("ChatSession", str(session_id))
        else:
            chat_session = ChatSession(
                meeting_id=meeting_id,
                user_id=user_id,
                title=request.question[:60],
            )
            db.add(chat_session)
            await db.flush()
            session_id = chat_session.id

        # 3. Retrieve relevant chunks via Hybrid Vector + Full-text search
        retrieved_chunks = await rag_service.retrieve_relevant_chunks(
            db, meeting_id=meeting_id, query=request.question, top_k=4
        )

        # 4. Build context string
        context_blocks = []
        sources: List[SourceCitation] = []

        if retrieved_chunks:
            for c in retrieved_chunks:
                ts_str = f"[{format_seconds_to_timestamp(c.start_time)} - {format_seconds_to_timestamp(c.end_time)}]"
                context_blocks.append(f"{ts_str} {c.speaker or 'Speaker 1'}: {c.text}")
                
                sources.append(
                    SourceCitation(
                        chunk_id=c.id,
                        speaker=c.speaker or "Speaker 1",
                        text=c.text,
                        start_time=c.start_time,
                        end_time=c.end_time,
                        formatted_timestamp=ts_str,
                    )
                )
            context_str = "\n\n".join(context_blocks)
        else:
            context_str = "No relevant meeting transcript segments found."

        # 5. Execute Grounded LLM Generation
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
            title=meeting.title,
            context=context_str,
            question=request.question,
        )

        try:
            llm_response = await ai_client_service.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            answer_text = llm_response.choices[0].message.content or "I couldn't find that information in this meeting."

        except Exception as e:
            logger.exception(f"OpenAI RAG generation failed for meeting={meeting_id}: {e}")
            raise AIProcessingException(f"Failed to generate answer: {str(e)}")

        # 6. Save User and Assistant Messages
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.question,
            sources=[],
        )
        db.add(user_msg)

        sources_payload = [s.model_dump(mode="json") for s in sources]
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer_text,
            sources=sources_payload,
        )
        db.add(assistant_msg)
        await db.flush()
        await db.refresh(assistant_msg)

        return AskMeetingResponse(
            answer=answer_text,
            sources=sources,
            session_id=session_id,
            message_id=assistant_msg.id,
        )

    @classmethod
    async def list_sessions(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        meeting_id: uuid.UUID,
    ) -> List[ChatSession]:
        await MeetingService.get_meeting(db, meeting_id, user_id)
        query = await db.execute(
            select(ChatSession)
            .where(ChatSession.meeting_id == meeting_id, ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
        )
        return list(query.scalars().all())

    @classmethod
    async def get_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        meeting_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> ChatSession:
        await MeetingService.get_meeting(db, meeting_id, user_id)
        query = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.meeting_id == meeting_id,
                ChatSession.user_id == user_id,
            )
        )
        session = query.scalar_one_or_none()
        if not session:
            raise EntityNotFoundException("ChatSession", str(session_id))
        return session


chat_service = ChatService()
