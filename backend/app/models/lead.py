from uuid import UUID
from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import LeadPriority, LeadStatus
from app.models.mixins import UUIDMixin, TimestampMixin


class Lead(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "leads"

    __table_args__ = (
        Index("ix_leads_created_at", "created_at"),
    )

    enquiry_id: Mapped[UUID] = mapped_column(
        ForeignKey("enquiries.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )

    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    priority: Mapped[LeadPriority] = mapped_column(
        Enum(LeadPriority),
        index=True,
        nullable=False,
    )

    intent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    suggested_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus),
        default=LeadStatus.NEW,
        index=True,
        nullable=False,
    )

    enquiry = relationship(
        "Enquiry",
        back_populates="lead",
    )

    follow_up_jobs = relationship(
        "FollowUpJob",
        back_populates="lead",
        cascade="all, delete-orphan",
    )