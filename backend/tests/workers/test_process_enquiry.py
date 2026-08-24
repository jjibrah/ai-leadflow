import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from arq import Retry

from app.models.ai_processing_result import AIProcessingResult
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus, LeadPriority
from app.services.ai.exceptions import (
    AIProviderError,
    AIResponseValidationError,
)
from app.services.ai.schemas import AIProcessingOutput
from app.workers.jobs.process_enquiry import (
    MAX_TRIES,
    process_enquiry_job,
    retry_delay,
)


class SessionContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def make_enquiry() -> Enquiry:
    return Enquiry(
        id=uuid4(),
        name="John Doe",
        email="john@example.com",
        company="Acme",
        message="We need an ERP system for our company.",
        source="website",
        status=EnquiryStatus.PENDING_PROCESSING,
    )


def make_output() -> AIProcessingOutput:
    return AIProcessingOutput(
        category="sales",
        priority="high",
        intent="ERP purchase",
        company="Acme",
        summary="Company evaluating an ERP system.",
        suggested_response="Thank you for contacting us.",
    )


class ProcessEnquiryJobTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_orchestrates_ai_result_and_lead(self):
        enquiry = make_enquiry()
        db = AsyncMock()
        ai_service = AsyncMock()
        ai_service.provider.model = "gemini-test"
        ai_service.process_enquiry.return_value = make_output()
        stored_result = AIProcessingResult(
            id=uuid4(),
            enquiry_id=enquiry.id,
            category="sales",
            priority=LeadPriority.HIGH,
            intent="ERP purchase",
            extracted_company="Acme",
            summary="Summary",
            suggested_response="Response",
            model_name="gemini-test",
        )

        async def create_lead(_db, *, enquiry, ai_result):
            enquiry.status = EnquiryStatus.PROCESSED

        with (
            patch(
                "app.workers.jobs.process_enquiry.AsyncSessionLocal",
                return_value=SessionContext(db),
            ),
            patch(
                "app.workers.jobs.process_enquiry.EnquiryRepository.get_by_id",
                new=AsyncMock(return_value=enquiry),
            ),
            patch(
                "app.workers.jobs.process_enquiry.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.workers.jobs.process_enquiry.AIProcessingResultRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.workers.jobs.process_enquiry.AIProcessingResultRepository.create",
                new=AsyncMock(return_value=stored_result),
            ) as create_result,
            patch(
                "app.workers.jobs.process_enquiry.LeadService.create_lead_from_enquiry",
                new=AsyncMock(side_effect=create_lead),
            ) as create_lead_mock,
        ):
            await process_enquiry_job(
                {"ai_service": ai_service, "job_try": 1},
                str(enquiry.id),
            )

        ai_service.process_enquiry.assert_awaited_once_with(enquiry)
        create_result.assert_awaited_once()
        create_lead_mock.assert_awaited_once()
        self.assertEqual(enquiry.status, EnquiryStatus.PROCESSED)

    async def test_existing_lead_makes_job_idempotent(self):
        enquiry = make_enquiry()
        db = AsyncMock()
        ai_service = AsyncMock()

        with (
            patch(
                "app.workers.jobs.process_enquiry.AsyncSessionLocal",
                return_value=SessionContext(db),
            ),
            patch(
                "app.workers.jobs.process_enquiry.EnquiryRepository.get_by_id",
                new=AsyncMock(return_value=enquiry),
            ),
            patch(
                "app.workers.jobs.process_enquiry.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=object()),
            ),
        ):
            await process_enquiry_job(
                {"ai_service": ai_service, "job_try": 1},
                str(enquiry.id),
            )

        ai_service.process_enquiry.assert_not_awaited()
        db.commit.assert_not_awaited()

    async def test_transient_failure_requests_delayed_retry(self):
        enquiry = make_enquiry()
        db = AsyncMock()
        ai_service = AsyncMock()
        ai_service.process_enquiry.side_effect = AIProviderError("temporary")

        with (
            patch(
                "app.workers.jobs.process_enquiry.AsyncSessionLocal",
                return_value=SessionContext(db),
            ),
            patch(
                "app.workers.jobs.process_enquiry.EnquiryRepository.get_by_id",
                new=AsyncMock(return_value=enquiry),
            ),
            patch(
                "app.workers.jobs.process_enquiry.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.workers.jobs.process_enquiry.AIProcessingResultRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
        ):
            with self.assertRaises(Retry) as raised:
                await process_enquiry_job(
                    {"ai_service": ai_service, "job_try": 2},
                    str(enquiry.id),
                )

        self.assertEqual(raised.exception.defer_score, 15_000)
        self.assertEqual(enquiry.status, EnquiryStatus.PROCESSING)

    async def test_retry_exhaustion_marks_enquiry_failed(self):
        enquiry = make_enquiry()
        db = AsyncMock()
        ai_service = AsyncMock()
        ai_service.process_enquiry.side_effect = AIProviderError("temporary")

        with (
            patch(
                "app.workers.jobs.process_enquiry.AsyncSessionLocal",
                return_value=SessionContext(db),
            ),
            patch(
                "app.workers.jobs.process_enquiry.EnquiryRepository.get_by_id",
                new=AsyncMock(return_value=enquiry),
            ),
            patch(
                "app.workers.jobs.process_enquiry.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.workers.jobs.process_enquiry.AIProcessingResultRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
        ):
            await process_enquiry_job(
                {"ai_service": ai_service, "job_try": MAX_TRIES},
                str(enquiry.id),
            )

        self.assertEqual(enquiry.status, EnquiryStatus.FAILED)
        self.assertEqual(
            enquiry.last_error,
            "AI processing failed after retry limit.",
        )

    async def test_validation_failure_does_not_retry(self):
        enquiry = make_enquiry()
        db = AsyncMock()
        ai_service = AsyncMock()
        ai_service.process_enquiry.side_effect = AIResponseValidationError(
            "invalid"
        )

        with (
            patch(
                "app.workers.jobs.process_enquiry.AsyncSessionLocal",
                return_value=SessionContext(db),
            ),
            patch(
                "app.workers.jobs.process_enquiry.EnquiryRepository.get_by_id",
                new=AsyncMock(return_value=enquiry),
            ),
            patch(
                "app.workers.jobs.process_enquiry.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.workers.jobs.process_enquiry.AIProcessingResultRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
        ):
            await process_enquiry_job(
                {"ai_service": ai_service, "job_try": 1},
                str(enquiry.id),
            )

        self.assertEqual(enquiry.status, EnquiryStatus.FAILED)
        self.assertEqual(enquiry.last_error, "AI response validation failed.")

    def test_retry_delay_is_bounded_exponential(self):
        self.assertEqual([retry_delay(i) for i in range(1, 6)], [5, 15, 45, 135, 300])


if __name__ == "__main__":
    unittest.main()
