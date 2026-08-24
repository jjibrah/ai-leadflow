from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.config import settings
from app.db.session import get_db
from app.models.enums import EnquiryStatus
from app.schemas.enquiry import EnquiryCreate, EnquiryResponse
from app.services.enquiry_service import EnquiryService
from app.workers.enqueue import enqueue_enquiry_processing


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
    redis: ArqRedis | None = Depends(get_redis),
):
    try:
        enquiry = await EnquiryService.create_enquiry(
            db=db,
            data=payload,
        )
        if settings.BACKGROUND_JOBS_ENABLED:
            enquiry.status = EnquiryStatus.PENDING_PROCESSING
        await db.commit()

        if settings.BACKGROUND_JOBS_ENABLED:
            if redis is None:
                raise RedisError("Redis connection is unavailable.")
            await enqueue_enquiry_processing(redis, enquiry.id)

        return EnquiryResponse(
            id=enquiry.id,
            status=enquiry.status.value,
            message="Enquiry submitted successfully.",
        )

    except SQLAlchemyError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to submit enquiry.",
        )

    except RedisError:
        enquiry.status = EnquiryStatus.FAILED
        enquiry.last_error = "Background processing unavailable."
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enquiry saved, but processing is temporarily unavailable.",
        )
