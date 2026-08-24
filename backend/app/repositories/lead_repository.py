from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.schemas.lead import LeadCreate


class LeadRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        data: LeadCreate,
    ) -> Lead:
        lead = Lead(**data.model_dump())
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def get_by_enquiry_id(
        db: AsyncSession,
        enquiry_id: UUID,
    ) -> Lead | None:
        result = await db.execute(
            select(Lead).where(Lead.enquiry_id == enquiry_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        lead_id: UUID,
    ) -> Lead | None:
        result = await db.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        lead: Lead,
        **changes,
    ) -> Lead:
        for field, value in changes.items():
            if not hasattr(lead, field):
                raise ValueError(f"Unknown lead field: {field}")
            setattr(lead, field, value)

        await db.flush()
        await db.refresh(lead)
        return lead
