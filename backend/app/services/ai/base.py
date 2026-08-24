from abc import ABC, abstractmethod

from app.services.ai.schemas import AIProcessingOutput


class AIProvider(ABC):

    @abstractmethod
    async def process_enquiry(
        self,
        *,
        name: str,
        email: str,
        company: str | None,
        message: str,
    ) -> AIProcessingOutput:
        raise NotImplementedError
