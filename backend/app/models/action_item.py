import uuid
from typing import Optional
from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ActionItem(Base, TimestampMixin):
    __tablename__ = "action_items"

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
    task: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    assignee: Mapped[str] = mapped_column(
        String(255),
        default="Not specified",
        nullable=False,
    )
    deadline: Mapped[str] = mapped_column(
        String(255),
        default="Not specified",
        nullable=False,
    )
    source_timestamp: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")
