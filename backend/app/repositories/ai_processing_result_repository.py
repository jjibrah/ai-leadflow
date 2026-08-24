from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_processing_result import AIProcessingResult
from app.models.enums import LeadPriority
from app.services.ai.schemas import AIProcessingOutput


class AIProcessingResultRepository:
    @staticmethod
    async def get_by_enquiry_id(
        db: AsyncSession,
        enquiry_id: UUID,
    ) -> AIProcessingResult | None:
        result = await db.execute(
            select(AIProcessingResult).where(
                AIProcessingResult.enquiry_id == enquiry_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        enquiry_id: UUID,
        result: AIProcessingOutput,
        model_name: str,
    ) -> AIProcessingResult:
        ai_result = AIProcessingResult(
            enquiry_id=enquiry_id,
            category=result.category,
            priority=LeadPriority(result.priority),
            intent=result.intent,
            extracted_company=result.company,
            summary=result.summary,
            suggested_response=result.suggested_response,
            model_name=model_name,
        )
        db.add(ai_result)
        await db.flush()
        return ai_result
