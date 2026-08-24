from typing import Protocol

from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.providers.openai_provider import OpenAIProvider
from app.services.ai.schemas import AIProcessingOutput


class EnquiryData(Protocol):
    name: str
    email: str
    company: str | None
    message: str


class AIService:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def process_enquiry(
        self,
        enquiry: EnquiryData,
    ) -> AIProcessingOutput:
        return await self.provider.process_enquiry(
            name=enquiry.name,
            email=enquiry.email,
            company=enquiry.company,
            message=enquiry.message,
        )


def create_ai_service() -> AIService:
    provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        timeout=settings.AI_TIMEOUT_SECONDS,
    )

    return AIService(provider)
