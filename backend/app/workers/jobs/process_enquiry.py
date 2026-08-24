from uuid import UUID

from arq import Retry
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus
from app.repositories.ai_processing_result_repository import (
    AIProcessingResultRepository,
)
from app.repositories.enquiry_repository import EnquiryRepository
from app.repositories.lead_repository import LeadRepository
from app.services.ai.exceptions import (
    AIProviderError,
    AIProviderTimeout,
    AIResponseValidationError,
)
from app.services.ai.service import AIService
from app.services.lead.exceptions import LeadProcessingError
from app.services.lead_service import LeadService


MAX_TRIES = 5


def retry_delay(job_try: int) -> int:
    return min(5 * (3 ** max(job_try - 1, 0)), 300)


async def mark_enquiry_failed(
    db,
    enquiry: Enquiry,
    error: str,
) -> None:
    enquiry.status = EnquiryStatus.FAILED
    enquiry.last_error = error[:500]
    await db.commit()


async def process_enquiry_job(
    ctx: dict,
    enquiry_id: str,
) -> None:
    try:
        parsed_enquiry_id = UUID(enquiry_id)
    except ValueError:
        return

    ai_service: AIService = ctx["ai_service"]

    async with AsyncSessionLocal() as db:
        enquiry = await EnquiryRepository.get_by_id(db, parsed_enquiry_id)
        if enquiry is None:
            return

        existing_lead = await LeadRepository.get_by_enquiry_id(
            db,
            parsed_enquiry_id,
        )
        if existing_lead is not None or enquiry.status == EnquiryStatus.PROCESSED:
            return

        enquiry.status = EnquiryStatus.PROCESSING
        enquiry.last_error = None
        await db.commit()

        try:
            stored_ai_result = (
                await AIProcessingResultRepository.get_by_enquiry_id(
                    db,
                    parsed_enquiry_id,
                )
            )

            if stored_ai_result is None:
                output = await ai_service.process_enquiry(enquiry)
                stored_ai_result = await AIProcessingResultRepository.create(
                    db,
                    enquiry_id=parsed_enquiry_id,
                    result=output,
                    model_name=getattr(ai_service.provider, "model", "unknown"),
                )

            await LeadService.create_lead_from_enquiry(
                db,
                enquiry=enquiry,
                ai_result=stored_ai_result,
            )

        except AIResponseValidationError:
            await db.rollback()
            await mark_enquiry_failed(
                db,
                enquiry,
                "AI response validation failed.",
            )

        except (AIProviderTimeout, AIProviderError):
            await db.rollback()
            job_try = int(ctx.get("job_try", 1))
            if job_try >= MAX_TRIES:
                await mark_enquiry_failed(
                    db,
                    enquiry,
                    "AI processing failed after retry limit.",
                )
                return

            raise Retry(defer=retry_delay(job_try))

        except (LeadProcessingError, SQLAlchemyError):
            await db.rollback()
            await mark_enquiry_failed(
                db,
                enquiry,
                "Lead processing failed.",
            )
