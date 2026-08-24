import asyncio
import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from app.services.ai.base import AIProvider
from app.services.ai.exceptions import (
    AIProviderError,
    AIProviderTimeout,
    AIResponseValidationError,
)
from app.services.ai.providers.openai_provider import OpenAIProvider
from app.services.ai.schemas import AIProcessingOutput
from app.services.ai.service import AIService


VALID_OUTPUT = {
    "category": "sales",
    "priority": "high",
    "intent": "Purchase an ERP system",
    "company": "ABC Logistics",
    "summary": "Logistics company evaluating an ERP system.",
    "suggested_response": "Thank you for your enquiry. Let's discuss your requirements.",
}


class FakeResponses:
    def __init__(self, *, output=VALID_OUTPUT, error=None, delay=0.0):
        self.output = output
        self.error = error
        self.delay = delay
        self.last_request = None

    async def parse(self, **kwargs):
        self.last_request = kwargs

        if self.delay:
            await asyncio.sleep(self.delay)

        if self.error:
            raise self.error

        return SimpleNamespace(output_parsed=self.output)


class FakeClient:
    def __init__(self, responses: FakeResponses):
        self.responses = responses


class FakeProvider(AIProvider):
    def __init__(self, output: AIProcessingOutput):
        self.output = output
        self.received = None

    async def process_enquiry(self, **kwargs) -> AIProcessingOutput:
        self.received = kwargs
        return self.output


class AIProcessingOutputTests(unittest.TestCase):
    def test_accepts_valid_output_and_strips_strings(self):
        output = AIProcessingOutput.model_validate(
            {
                **VALID_OUTPUT,
                "intent": "  Purchase an ERP system  ",
                "company": "   ",
            }
        )

        self.assertEqual(output.intent, "Purchase an ERP system")
        self.assertIsNone(output.company)

    def test_rejects_unknown_category(self):
        with self.assertRaises(ValidationError):
            AIProcessingOutput.model_validate(
                {**VALID_OUTPUT, "category": "billing"}
            )

    def test_rejects_invalid_priority(self):
        with self.assertRaises(ValidationError):
            AIProcessingOutput.model_validate(
                {**VALID_OUTPUT, "priority": "urgent"}
            )

    def test_rejects_whitespace_only_required_text(self):
        with self.assertRaises(ValidationError):
            AIProcessingOutput.model_validate(
                {**VALID_OUTPUT, "summary": "   "}
            )

    def test_rejects_unexpected_fields(self):
        with self.assertRaises(ValidationError):
            AIProcessingOutput.model_validate(
                {**VALID_OUTPUT, "confidence": 0.95}
            )


class OpenAIProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_validated_structured_output(self):
        responses = FakeResponses()
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(responses),
        )

        result = await provider.process_enquiry(
            name="John Doe",
            email="john@example.com",
            company="ABC Logistics",
            message="We need an ERP solution for our logistics company.",
        )

        self.assertEqual(result.category, "sales")
        self.assertEqual(result.priority, "high")
        self.assertEqual(responses.last_request["model"], "test-model")
        self.assertIs(
            responses.last_request["text_format"],
            AIProcessingOutput,
        )
        self.assertFalse(responses.last_request["store"])

    async def test_rejects_malformed_structured_output(self):
        responses = FakeResponses(
            output={**VALID_OUTPUT, "priority": "urgent"}
        )
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(responses),
        )

        with self.assertRaises(AIResponseValidationError):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="Please tell me about your ERP product.",
            )

    async def test_rejects_missing_structured_output(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(FakeResponses(output=None)),
        )

        with self.assertRaises(AIResponseValidationError):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="Please tell me about your ERP product.",
            )

    async def test_translates_timeout(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            timeout=0.001,
            client=FakeClient(FakeResponses(delay=0.05)),
        )

        with self.assertRaises(AIProviderTimeout):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="Please tell me about your ERP product.",
            )

    async def test_translates_provider_failure(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(
                FakeResponses(error=RuntimeError("provider detail"))
            ),
        )

        with self.assertRaisesRegex(
            AIProviderError,
            "AI provider request failed",
        ):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="Please tell me about your ERP product.",
            )


class AIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_an_enquiry_and_delegates_to_provider(self):
        expected = AIProcessingOutput.model_validate(VALID_OUTPUT)
        provider = FakeProvider(expected)
        service = AIService(provider)
        enquiry = SimpleNamespace(
            name="John Doe",
            email="john@example.com",
            company="ABC Logistics",
            message="We need an ERP solution.",
        )

        result = await service.process_enquiry(enquiry)

        self.assertEqual(result, expected)
        self.assertEqual(provider.received["email"], enquiry.email)


if __name__ == "__main__":
    unittest.main()
