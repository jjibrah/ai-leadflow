from app.services.ai.base import AIProvider
from app.services.ai.schemas import AIProcessingOutput


class AIService:

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def process_enquiry(
        self,
        name: str,
        email: str,
        company: str | None,
        message: str,
    ) -> AIProcessingOutput:

        return await self.provider.process_enquiry(
            name=name,
            email=email,
            company=company,
            message=message,
        )