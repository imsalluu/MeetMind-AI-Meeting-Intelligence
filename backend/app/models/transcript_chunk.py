import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base, TimestampMixin

# Use JSONB for Postgres and JSON for SQLite compatibility
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class TranscriptChunk(Base, TimestampMixin):
    __tablename__ = "transcript_chunks"

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
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    speaker: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    start_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    end_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    embedding = mapped_column(
        Vector(1536),
        nullable=True,
    )
    metadata_json = mapped_column(
        JSON_TYPE,
        nullable=True,
        default=dict,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="transcript_chunks")
