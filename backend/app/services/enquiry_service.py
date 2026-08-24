from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.enquiry_repository import EnquiryRepository
from app.schemas.enquiry import EnquiryCreate


class EnquiryService:

    @staticmethod
    async def create_enquiry(
        db: AsyncSession,
        data: EnquiryCreate,
    ):
        return await EnquiryRepository.create(
            db,
            name=data.name,
            email=str(data.email),
            company=data.company,
            message=data.message,
        )