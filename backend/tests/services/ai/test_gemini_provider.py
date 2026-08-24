import asyncio
import unittest
from types import SimpleNamespace

from app.services.ai.exceptions import (
    AIProviderError,
    AIProviderTimeout,
    AIResponseValidationError,
)
from app.services.ai.providers.gemini_provider import GeminiProvider
from app.services.ai.schemas import AIProcessingOutput


VALID_OUTPUT = {
    "category": "sales",
    "priority": "high",
    "intent": "Purchase an ERP system",
    "company": "ABC Logistics",
    "summary": "Logistics company evaluating an ERP system.",
    "suggested_response": "Thank you for your enquiry. Let's discuss your requirements.",
}


class FakeModels:
    def __init__(
        self,
        *,
        parsed=VALID_OUTPUT,
        text=None,
        error=None,
        delay=0.0,
    ):
        self.parsed = parsed
        self.text = text
        self.error = error
        self.delay = delay
        self.last_request = None

    async def generate_content(self, **kwargs):
        self.last_request = kwargs

        if self.delay:
            await asyncio.sleep(self.delay)

        if self.error:
            raise self.error

        return SimpleNamespace(parsed=self.parsed, text=self.text)


class FakeClient:
    def __init__(self, models: FakeModels):
        self.aio = SimpleNamespace(models=models)


class GeminiProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_validated_structured_output(self):
        models = FakeModels()
        provider = GeminiProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(models),
        )

        result = await provider.process_enquiry(
            name="John Doe",
            email="john@example.com",
            company="ABC Logistics",
            message="We need an ERP solution.",
        )

        self.assertEqual(result.category, "sales")
        self.assertEqual(result.priority, "high")
        self.assertEqual(models.last_request["model"], "test-model")
        config = models.last_request["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertNotIn(
            "additionalProperties",
            config.response_schema,
        )
        self.assertEqual(
            config.response_schema["properties"]["priority"]["enum"],
            ["low", "medium", "high"],
        )

    async def test_validates_json_text_fallback(self):
        output = AIProcessingOutput.model_validate(VALID_OUTPUT)
        provider = GeminiProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(
                FakeModels(parsed=None, text=output.model_dump_json())
            ),
        )

        result = await provider.process_enquiry(
            name="John Doe",
            email="john@example.com",
            company=None,
            message="We need an ERP solution.",
        )

        self.assertEqual(result, output)

    async def test_rejects_malformed_output(self):
        provider = GeminiProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(
                FakeModels(parsed={**VALID_OUTPUT, "priority": "urgent"})
            ),
        )

        with self.assertRaises(AIResponseValidationError):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="We need an ERP solution.",
            )

    async def test_rejects_missing_output(self):
        provider = GeminiProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(FakeModels(parsed=None, text=None)),
        )

        with self.assertRaises(AIResponseValidationError):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="We need an ERP solution.",
            )

    async def test_translates_timeout(self):
        provider = GeminiProvider(
            api_key="test-key",
            model="test-model",
            timeout=0.001,
            client=FakeClient(FakeModels(delay=0.05)),
        )

        with self.assertRaises(AIProviderTimeout):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="We need an ERP solution.",
            )

    async def test_translates_provider_failure(self):
        provider = GeminiProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient(FakeModels(error=RuntimeError("details"))),
        )

        with self.assertRaises(AIProviderError):
            await provider.process_enquiry(
                name="John Doe",
                email="john@example.com",
                company=None,
                message="We need an ERP solution.",
            )


if __name__ == "__main__":
    unittest.main()
