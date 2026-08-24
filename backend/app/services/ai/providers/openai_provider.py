import asyncio
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI
from pydantic import ValidationError

from app.services.ai.base import AIProvider
from app.services.ai.exceptions import (
    AIProviderError,
    AIProviderTimeout,
    AIResponseValidationError,
)
from app.services.ai.schemas import AIProcessingOutput


class OpenAIProvider(AIProvider):
    SYSTEM_INSTRUCTIONS = """
You analyse customer enquiries for LeadFlow.

Return structured lead intelligence grounded only in the supplied enquiry.
The category must be one of: sales, support, partnership, general, spam.

Priority rules:
- high: urgent buying intent, serious commercial interest, an immediate
  support issue, or another immediate business need
- medium: legitimate interest or a request without immediate urgency
- low: a general enquiry, weak commercial intent, an informational request,
  or spam

Do not invent unsupported facts. Keep the summary concise and make the
suggested response professional and directly relevant to the enquiry.
""".strip()

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 25.0,
        client: Any | None = None,
    ):
        self.client = client or AsyncOpenAI(api_key=api_key)
        self.model = model
        self.timeout = timeout

    @staticmethod
    def _build_input(
        *,
        name: str,
        email: str,
        company: str | None,
        message: str,
    ) -> str:
        return f"""
Customer enquiry

Name: {name}
Email: {email}
Company: {company or "Not provided"}

Message:
{message}
""".strip()

    async def process_enquiry(
        self,
        *,
        name: str,
        email: str,
        company: str | None,
        message: str,
    ) -> AIProcessingOutput:
        enquiry_input = self._build_input(
            name=name,
            email=email,
            company=company,
            message=message,
        )

        try:
            async with asyncio.timeout(self.timeout):
                response = await self.client.responses.parse(
                    model=self.model,
                    instructions=self.SYSTEM_INSTRUCTIONS,
                    input=enquiry_input,
                    text_format=AIProcessingOutput,
                    store=False,
                )

            if response.output_parsed is None:
                raise AIResponseValidationError(
                    "AI provider returned no structured output."
                )

            return AIProcessingOutput.model_validate(response.output_parsed)

        except (TimeoutError, APITimeoutError) as exc:
            raise AIProviderTimeout(
                "AI provider request timed out."
            ) from exc

        except ValidationError as exc:
            raise AIResponseValidationError(
                "AI provider returned invalid structured output."
            ) from exc

        except AIResponseValidationError:
            raise

        except APIError as exc:
            raise AIProviderError(
                "AI provider request failed."
            ) from exc

        except Exception as exc:
            raise AIProviderError(
                "AI provider request failed."
            ) from exc
