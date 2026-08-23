from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import EnquiryStatus
from app.models.mixins import UUIDMixin, TimestampMixin


class Enquiry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "enquiries"

    __table_args__ = (
        Index("ix_enquiries_created_at", "created_at"),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str]=mapped_column(
        Text,
        nullable=False,
    )


    source: Mapped[str]=mapped_column(
        String(100),
        nullable=False,
        default="website",
    )
    ai_processing_result = relationship(
        "AIProcessingResult",
        back_populates="enquiry",
        uselist=False,
        cascade="all, delete-orphan",
    )

    lead = relationship(
        "Lead",
        back_populates="enquiry",
        uselist=False,
        cascade="all, delete-orphan",
    )

    webhook_events = relationship(
        "WebhookEvent",
        back_populates="enquiry",
    )

    status: Mapped[EnquiryStatus] = mapped_column(
        Enum(
            EnquiryStatus,
            values_callable=lambda enum: [item.value for item in enum],
            name="enquiry_status",
        ),
        default=EnquiryStatus.RECEIVED,
        nullable=False,
        index=True,
    )
