from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus


class EnquiryRepository:

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
