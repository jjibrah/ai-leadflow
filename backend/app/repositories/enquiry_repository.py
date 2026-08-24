from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enquiry import Enquiry


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
            status="received",
        )

        db.add(enquiry)

        await db.commit()
        await db.refresh(enquiry)

        return enquiry