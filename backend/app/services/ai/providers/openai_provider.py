import asyncio

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.services.ai.base import AIProvider
from app.services.ai.schemas import AIProcessingOutput
from app.services.ai.exceptions import (
    AIProviderError,
    AIProviderTimeout,
    AIResponseValidationError,
)

class OpenAIProvider(AIProvider):

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 25.0,
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.timeout = timeout

def _build_prompt(
    self,
    name: str,
    email: str,
    company: str | None,
    message: str,
) -> str:

    return f"""
Analyse the following customer enquiry.

Customer:
Name: {name}
Email: {email}
Company: {company or "Not provided"}

Message:
{message}

Classify the enquiry into exactly one category:

- sales
- support
- partnership
- general
- spam

Determine priority:

- high: urgent buying intent, serious commercial interest,
  immediate support issue, or immediate business need

- medium: legitimate interest or request but without
  immediate urgency

- low: general enquiry, weak commercial intent,
  informational request, or spam

Determine:

- category
- priority
- customer intent
- company
- concise summary
- suggested professional response

Do not invent information that is not supported by the enquiry.
"""
async def process_enquiry(
    self,
    name: str,
    email: str,
    company: str | None,
    message: str,
) -> AIProcessingOutput:

    prompt = self._build_prompt(
        name=name,
        email=email,
        company=company,
        message=message,
    )

    try:

        response = await asyncio.wait_for(
            self.client.responses.parse(
                model=self.model,
                input=prompt,
                text_format=AIProcessingOutput,
            ),
            timeout=self.timeout,
        )

        result = response.output_parsed

        if result is None:
            raise AIResponseValidationError(
                "AI provider returned no structured output."
            )

        return result

    except asyncio.TimeoutError as exc:
        raise AIProviderTimeout(
            "AI provider request timed out."
        ) from exc

    except ValidationError as exc:
        raise AIResponseValidationError(
            "AI provider returned invalid structured output."
        ) from exc

    except AIResponseValidationError:
        raise

    except Exception as exc:
        raise AIProviderError(
            "AI provider request failed."
        ) from exc