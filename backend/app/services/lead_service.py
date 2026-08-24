from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_processing_result import AIProcessingResult
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus, LeadPriority, LeadStatus
from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate
from app.services.ai.schemas import AIProcessingOutput
from app.services.lead.exceptions import (
    EnquiryNotReadyError,
    InvalidAIResultError,
    InvalidLeadStatusTransitionError,
    LeadPersistenceError,
    MissingAIResultError,
)


class LeadService:
    STATUS_TRANSITIONS = {
        LeadStatus.NEW: LeadStatus.CONTACTED,
        LeadStatus.CONTACTED: LeadStatus.QUALIFIED,
        LeadStatus.QUALIFIED: LeadStatus.CLOSED,
    }

    @staticmethod
    def _validate_ai_result(
        enquiry: Enquiry,
        ai_result: AIProcessingResult | None,
    ) -> AIProcessingOutput:
        if ai_result is None:
            raise MissingAIResultError(
                "A validated AI result is required to create a lead."
            )

        if ai_result.enquiry_id != enquiry.id:
            raise InvalidAIResultError(
                "The AI result does not belong to this enquiry."
            )

        priority = ai_result.priority
        if isinstance(priority, LeadPriority):
            priority = priority.value

        try:
            return AIProcessingOutput.model_validate(
                {
                    "category": ai_result.category,
                    "priority": priority,
                    "intent": ai_result.intent,
                    "company": ai_result.extracted_company,
                    "summary": ai_result.summary,
                    "suggested_response": ai_result.suggested_response,
                }
            )
        except ValidationError as exc:
            raise InvalidAIResultError(
                "The stored AI result is incomplete or invalid."
            ) from exc

    @staticmethod
    async def create_lead_from_enquiry(
        db: AsyncSession,
        *,
        enquiry: Enquiry,
        ai_result: AIProcessingResult | None,
    ) -> Lead:
        enquiry_id = enquiry.id
        existing_lead = await LeadRepository.get_by_enquiry_id(
            db,
            enquiry_id,
        )

        if existing_lead is not None:
            return existing_lead

        validated_ai = LeadService._validate_ai_result(
            enquiry,
            ai_result,
        )

        if enquiry.status != EnquiryStatus.PROCESSING:
            raise EnquiryNotReadyError(
                "The enquiry must be processing before lead creation."
            )

        lead_data = LeadCreate(
            enquiry_id=enquiry_id,
            name=enquiry.name,
            email=enquiry.email,
            company=validated_ai.company or enquiry.company,
            category=validated_ai.category,
            priority=LeadPriority(validated_ai.priority),
            intent=validated_ai.intent,
            summary=validated_ai.summary,
            suggested_response=validated_ai.suggested_response,
            status=LeadStatus.NEW,
        )

        original_status = enquiry.status

        try:
            lead = await LeadRepository.create(db, lead_data)
            enquiry.status = EnquiryStatus.PROCESSED
            await db.commit()
            return lead

        except IntegrityError as exc:
            await db.rollback()
            existing_lead = await LeadRepository.get_by_enquiry_id(
                db,
                enquiry_id,
            )

            if existing_lead is not None:
                enquiry.status = EnquiryStatus.PROCESSED
                return existing_lead

            enquiry.status = original_status
            raise LeadPersistenceError(
                "Unable to create lead."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()
            enquiry.status = original_status
            raise LeadPersistenceError(
                "Unable to create lead."
            ) from exc

    @staticmethod
    async def update_status(
        db: AsyncSession,
        *,
        lead: Lead,
        new_status: LeadStatus,
    ) -> Lead:
        if lead.status == new_status:
            return lead

        expected_status = LeadService.STATUS_TRANSITIONS.get(lead.status)
        if expected_status != new_status:
            raise InvalidLeadStatusTransitionError(
                f"Cannot move lead from {lead.status.value} to {new_status.value}."
            )

        original_status = lead.status

        try:
            updated_lead = await LeadRepository.update(
                db,
                lead,
                status=new_status,
            )
            await db.commit()
            return updated_lead
        except SQLAlchemyError as exc:
            await db.rollback()
            lead.status = original_status
            raise LeadPersistenceError(
                "Unable to update lead status."
            ) from exc
