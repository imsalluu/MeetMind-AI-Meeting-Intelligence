import json
import uuid
from typing import List
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import AIProcessingException
from app.core.logging import logger
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting import Meeting
from app.models.meeting_insight import MeetingInsight
from app.models.meeting_topic import MeetingTopic
from app.models.transcript import TranscriptSegment
from app.prompts.intelligence import INTELLIGENCE_SYSTEM_PROMPT, INTELLIGENCE_USER_PROMPT_TEMPLATE
from app.schemas.intelligence import MeetingIntelligenceOutput
from app.schemas.transcript import format_seconds_to_timestamp
from app.services.ai.llm import ai_client_service


class MeetingAnalyzerService:
    """Centralized AI meeting intelligence analyzer utilizing structured LLM generation."""

    @staticmethod
    def format_transcript_context(segments: List[TranscriptSegment]) -> str:
        """Format segments with speaker tags and exact timestamp intervals."""
        formatted_lines = []
        for seg in segments:
            start_str = format_seconds_to_timestamp(seg.start_time)
            end_str = format_seconds_to_timestamp(seg.end_time)
            formatted_lines.append(f"[{start_str} - {end_str}] {seg.speaker} (at {seg.start_time:.1f}s): {seg.text}")
        return "\n".join(formatted_lines)

    @classmethod
    async def analyze_meeting(
        cls,
        db: AsyncSession,
        meeting: Meeting,
        segments: List[TranscriptSegment],
    ) -> MeetingIntelligenceOutput:
        if not segments:
            raise AIProcessingException("Cannot analyze meeting with empty transcript.")

        formatted_transcript = cls.format_transcript_context(segments)
        user_prompt = INTELLIGENCE_USER_PROMPT_TEMPLATE.format(
            title=meeting.title,
            description=meeting.description or "No description provided",
            formatted_transcript=formatted_transcript,
        )

        logger.info(f"Generating meeting intelligence for meeting={meeting.id} using model={settings.OPENAI_MODEL}")

        try:
            response = await ai_client_service.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": INTELLIGENCE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_content = response.choices[0].message.content or "{}"
            parsed_data = MeetingIntelligenceOutput.model_validate_json(raw_content)

        except Exception as e:
            logger.exception(f"OpenAI Meeting Intelligence analysis failed for meeting={meeting.id}: {e}")
            raise AIProcessingException(f"Failed to generate meeting intelligence: {str(e)}")

        # Clean old insight, action items, decisions, and topics for idempotency
        await db.execute(delete(MeetingInsight).where(MeetingInsight.meeting_id == meeting.id))
        await db.execute(delete(ActionItem).where(ActionItem.meeting_id == meeting.id))
        await db.execute(delete(Decision).where(Decision.meeting_id == meeting.id))
        await db.execute(delete(MeetingTopic).where(MeetingTopic.meeting_id == meeting.id))

        # 1. Save MeetingInsight
        insight = MeetingInsight(
            meeting_id=meeting.id,
            executive_summary=parsed_data.executive_summary,
            short_summary=parsed_data.short_summary,
            detailed_summary=parsed_data.detailed_summary,
            key_points=parsed_data.key_points,
            risks=parsed_data.risks,
            questions=parsed_data.questions,
        )
        db.add(insight)

        # 2. Save Action Items
        for item in parsed_data.action_items:
            action = ActionItem(
                meeting_id=meeting.id,
                task=item.task,
                assignee=item.assignee or "Not specified",
                deadline=item.deadline or "Not specified",
                source_timestamp=item.source_timestamp,
                is_completed=False,
            )
            db.add(action)

        # 3. Save Decisions
        for dec in parsed_data.decisions:
            decision = Decision(
                meeting_id=meeting.id,
                decision=dec.decision,
                source_timestamp=dec.source_timestamp,
            )
            db.add(decision)

        # 4. Save Topics
        for top in parsed_data.topics:
            topic = MeetingTopic(
                meeting_id=meeting.id,
                topic=top.topic,
                summary=top.summary,
            )
            db.add(topic)

        await db.flush()
        logger.info(
            f"Saved meeting intelligence for meeting={meeting.id}: {len(parsed_data.action_items)} actions, {len(parsed_data.decisions)} decisions, {len(parsed_data.topics)} topics"
        )
        return parsed_data


meeting_analyzer_service = MeetingAnalyzerService()
