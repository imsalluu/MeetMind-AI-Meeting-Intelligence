import enum
import uuid
from sqlalchemy import BigInteger, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class MeetingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingStage(str, enum.Enum):
    UPLOADING = "UPLOADING"
    TRANSCRIBING = "TRANSCRIBING"
    ANALYZING = "ANALYZING"
    INDEXING = "INDEXING"
    READY = "READY"
    ERROR = "ERROR"


class Meeting(Base, TimestampMixin):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    audio_path: Mapped[str] = mapped_column(
        String(512),
        nullable=True,
    )
    audio_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True,
    )
    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=MeetingStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    processing_stage: Mapped[str] = mapped_column(
        String(50),
        default=ProcessingStage.UPLOADING.value,
        nullable=True,
    )
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships with selectin lazy loading for async SQLAlchemy
    user = relationship("User", back_populates="meetings", lazy="selectin")
    transcript_segments = relationship(
        "TranscriptSegment",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.start_time",
        lazy="selectin",
    )
    transcript_chunks = relationship(
        "TranscriptChunk",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptChunk.chunk_index",
        lazy="selectin",
    )
    action_items = relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    decisions = relationship(
        "Decision",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    topics = relationship(
        "MeetingTopic",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    insight = relationship(
        "MeetingInsight",
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    chat_sessions = relationship(
        "ChatSession",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
