from typing import Protocol

from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.exceptions import AIConfigurationError
from app.services.ai.providers.gemini_provider import GeminiProvider
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
    if settings.AI_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise AIConfigurationError(
                "GEMINI_API_KEY is required when AI_PROVIDER=gemini."
            )

        provider: AIProvider = GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
        )
    else:
        if not settings.OPENAI_API_KEY:
            raise AIConfigurationError(
                "OPENAI_API_KEY is required when AI_PROVIDER=openai."
            )

        provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
        )

    return AIService(provider)
