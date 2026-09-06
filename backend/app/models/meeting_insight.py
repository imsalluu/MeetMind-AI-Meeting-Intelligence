import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class MeetingInsight(Base, TimestampMixin):
    __tablename__ = "meeting_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    executive_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    short_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    detailed_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    key_points = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )
    risks = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )
    questions = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="insight")
