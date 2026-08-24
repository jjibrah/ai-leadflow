from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.enquiry import EnquiryCreate, EnquiryResponse
from app.services.enquiry_service import EnquiryService


router = APIRouter(
    prefix="/enquiries",
    tags=["Enquiries"],
)


@router.post(
    "",
    response_model=EnquiryResponse,
    status_code=status.HTTP_201_CREATED,
)

async def create_enquiry(
    payload: EnquiryCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        enquiry = await EnquiryService.create_enquiry(
            db=db,
            data=payload,
        )

        await db.commit()

        return EnquiryResponse(
            id=enquiry.id,
            status="received",
            message="Enquiry submitted successfully.",
        )

    except SQLAlchemyError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to submit enquiry.",
        )
