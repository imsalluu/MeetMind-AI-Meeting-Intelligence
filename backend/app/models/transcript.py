import uuid
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class TranscriptSegment(Base, TimestampMixin):
    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    speaker: Mapped[str] = mapped_column(
        String(100),
        default="Speaker 1",
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    start_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    end_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )
    segment_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="transcript_segments")
