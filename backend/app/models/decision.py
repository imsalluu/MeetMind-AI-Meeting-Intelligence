import uuid
from typing import Optional
from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Decision(Base, TimestampMixin):
    __tablename__ = "decisions"

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
    decision: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_timestamp: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="decisions")
