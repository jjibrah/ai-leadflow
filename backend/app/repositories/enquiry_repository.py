from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus


class EnquiryRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        enquiry_id: UUID,
    ) -> Enquiry | None:
        result = await db.execute(
            select(Enquiry).where(Enquiry.id == enquiry_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        name: str,
        email: str,
        company: str | None,
        message: str,
    ) -> Enquiry:

        enquiry = Enquiry(
            name=name,
            email=email,
            company=company,
            message=message,
            source="website",
            status=EnquiryStatus.RECEIVED,
        )

        db.add(enquiry)

        await db.flush()
        await db.refresh(enquiry)

        return enquiry
