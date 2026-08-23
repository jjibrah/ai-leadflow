from uuid import UUID
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import LeadPriority
from app.models.mixins import UUIDMixin, TimestampMixin


class AIProcessingResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_processing_results"

    enquiry_id: Mapped[UUID] = mapped_column(
        ForeignKey("enquiries.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    priority: Mapped[LeadPriority] = mapped_column(
        nullable=False,
    )

    intent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    extracted_company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    suggested_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    enquiry = relationship(
        "Enquiry",
        back_populates="ai_processing_result",
    )