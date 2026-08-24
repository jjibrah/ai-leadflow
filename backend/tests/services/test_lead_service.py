import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.ai_processing_result import AIProcessingResult
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus, LeadPriority, LeadStatus
from app.models.lead import Lead
from app.services.lead.exceptions import (
    EnquiryNotReadyError,
    InvalidAIResultError,
    InvalidLeadStatusTransitionError,
    LeadPersistenceError,
    MissingAIResultError,
)
from app.services.lead_service import LeadService


def make_enquiry(
    *,
    status: EnquiryStatus = EnquiryStatus.PROCESSING,
    company: str | None = "Fallback Logistics",
) -> Enquiry:
    return Enquiry(
        id=uuid4(),
        name="John Doe",
        email="john@example.com",
        company=company,
        message="We need an ERP solution for our logistics company.",
        source="website",
        status=status,
    )


def make_ai_result(
    enquiry: Enquiry,
    *,
    extracted_company: str | None = "AI Logistics",
    category: str = "sales",
) -> AIProcessingResult:
    return AIProcessingResult(
        id=uuid4(),
        enquiry_id=enquiry.id,
        category=category,
        priority=LeadPriority.HIGH,
        intent="Purchase an ERP system",
        extracted_company=extracted_company,
        summary="Logistics company evaluating an ERP solution.",
        suggested_response="Thank you for reaching out. Let's discuss your needs.",
        model_name="gemini-3.5-flash",
    )


def make_lead(
    enquiry: Enquiry,
    *,
    status: LeadStatus = LeadStatus.NEW,
) -> Lead:
    return Lead(
        id=uuid4(),
        enquiry_id=enquiry.id,
        name=enquiry.name,
        email=enquiry.email,
        company=enquiry.company,
        category="sales",
        priority=LeadPriority.HIGH,
        intent="Purchase an ERP system",
        summary="Summary",
        suggested_response="Response",
        status=status,
    )


class LeadCreationTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_lead_and_marks_enquiry_processed(self):
        enquiry = make_enquiry()
        ai_result = make_ai_result(enquiry)
        db = AsyncMock()
        captured_data = None

        async def create_lead(_db, data):
            nonlocal captured_data
            captured_data = data
            return Lead(id=uuid4(), **data.model_dump())

        with (
            patch(
                "app.services.lead_service.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.lead_service.LeadRepository.create",
                new=AsyncMock(side_effect=create_lead),
            ),
        ):
            lead = await LeadService.create_lead_from_enquiry(
                db,
                enquiry=enquiry,
                ai_result=ai_result,
            )

        self.assertEqual(lead.enquiry_id, enquiry.id)
        self.assertEqual(captured_data.company, "AI Logistics")
        self.assertEqual(captured_data.category, "sales")
        self.assertEqual(captured_data.priority, LeadPriority.HIGH)
        self.assertEqual(captured_data.intent, ai_result.intent)
        self.assertEqual(captured_data.summary, ai_result.summary)
        self.assertEqual(
            captured_data.suggested_response,
            ai_result.suggested_response,
        )
        self.assertEqual(captured_data.status, LeadStatus.NEW)
        self.assertEqual(enquiry.status, EnquiryStatus.PROCESSED)
        db.commit.assert_awaited_once()

    async def test_falls_back_to_enquiry_company(self):
        enquiry = make_enquiry(company="Fallback Logistics")
        ai_result = make_ai_result(enquiry, extracted_company=None)
        db = AsyncMock()
        captured_data = None

        async def create_lead(_db, data):
            nonlocal captured_data
            captured_data = data
            return Lead(id=uuid4(), **data.model_dump())

        with (
            patch(
                "app.services.lead_service.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.lead_service.LeadRepository.create",
                new=AsyncMock(side_effect=create_lead),
            ),
        ):
            await LeadService.create_lead_from_enquiry(
                db,
                enquiry=enquiry,
                ai_result=ai_result,
            )

        self.assertEqual(captured_data.company, "Fallback Logistics")

    async def test_duplicate_processing_returns_existing_lead(self):
        enquiry = make_enquiry(status=EnquiryStatus.PROCESSED)
        existing = make_lead(enquiry)
        db = AsyncMock()

        with patch(
            "app.services.lead_service.LeadRepository.get_by_enquiry_id",
            new=AsyncMock(return_value=existing),
        ):
            result = await LeadService.create_lead_from_enquiry(
                db,
                enquiry=enquiry,
                ai_result=None,
            )

        self.assertIs(result, existing)
        db.commit.assert_not_awaited()

    async def test_missing_ai_result_fails_safely(self):
        enquiry = make_enquiry()

        with patch(
            "app.services.lead_service.LeadRepository.get_by_enquiry_id",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(MissingAIResultError):
                await LeadService.create_lead_from_enquiry(
                    AsyncMock(),
                    enquiry=enquiry,
                    ai_result=None,
                )

    async def test_ai_result_must_belong_to_enquiry(self):
        enquiry = make_enquiry()
        ai_result = make_ai_result(enquiry)
        ai_result.enquiry_id = uuid4()

        with patch(
            "app.services.lead_service.LeadRepository.get_by_enquiry_id",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(InvalidAIResultError):
                await LeadService.create_lead_from_enquiry(
                    AsyncMock(),
                    enquiry=enquiry,
                    ai_result=ai_result,
                )

    async def test_invalid_ai_output_fails_safely(self):
        enquiry = make_enquiry()
        ai_result = make_ai_result(enquiry, category="unknown")

        with patch(
            "app.services.lead_service.LeadRepository.get_by_enquiry_id",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(InvalidAIResultError):
                await LeadService.create_lead_from_enquiry(
                    AsyncMock(),
                    enquiry=enquiry,
                    ai_result=ai_result,
                )

    async def test_enquiry_must_be_processing(self):
        enquiry = make_enquiry(status=EnquiryStatus.RECEIVED)

        with patch(
            "app.services.lead_service.LeadRepository.get_by_enquiry_id",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(EnquiryNotReadyError):
                await LeadService.create_lead_from_enquiry(
                    AsyncMock(),
                    enquiry=enquiry,
                    ai_result=make_ai_result(enquiry),
                )

    async def test_database_failure_does_not_mark_enquiry_processed(self):
        enquiry = make_enquiry()
        db = AsyncMock()

        with (
            patch(
                "app.services.lead_service.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.lead_service.LeadRepository.create",
                new=AsyncMock(side_effect=SQLAlchemyError("failure")),
            ),
        ):
            with self.assertRaises(LeadPersistenceError):
                await LeadService.create_lead_from_enquiry(
                    db,
                    enquiry=enquiry,
                    ai_result=make_ai_result(enquiry),
                )

        self.assertEqual(enquiry.status, EnquiryStatus.PROCESSING)
        db.rollback.assert_awaited_once()

    async def test_unique_race_returns_winning_lead(self):
        enquiry = make_enquiry()
        winner = make_lead(enquiry)
        db = AsyncMock()

        with (
            patch(
                "app.services.lead_service.LeadRepository.get_by_enquiry_id",
                new=AsyncMock(side_effect=[None, winner]),
            ),
            patch(
                "app.services.lead_service.LeadRepository.create",
                new=AsyncMock(
                    side_effect=IntegrityError(
                        "insert",
                        {},
                        Exception("duplicate"),
                    )
                ),
            ),
        ):
            result = await LeadService.create_lead_from_enquiry(
                db,
                enquiry=enquiry,
                ai_result=make_ai_result(enquiry),
            )

        self.assertIs(result, winner)
        self.assertEqual(enquiry.status, EnquiryStatus.PROCESSED)
        db.rollback.assert_awaited_once()


class LeadStatusLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_allows_next_status_transition(self):
        enquiry = make_enquiry()
        lead = make_lead(enquiry, status=LeadStatus.NEW)
        db = AsyncMock()

        async def update(_db, current_lead, **changes):
            current_lead.status = changes["status"]
            return current_lead

        with patch(
            "app.services.lead_service.LeadRepository.update",
            new=AsyncMock(side_effect=update),
        ):
            result = await LeadService.update_status(
                db,
                lead=lead,
                new_status=LeadStatus.CONTACTED,
            )

        self.assertEqual(result.status, LeadStatus.CONTACTED)
        db.commit.assert_awaited_once()

    async def test_rejects_skipped_status_transition(self):
        enquiry = make_enquiry()
        lead = make_lead(enquiry, status=LeadStatus.NEW)

        with self.assertRaises(InvalidLeadStatusTransitionError):
            await LeadService.update_status(
                AsyncMock(),
                lead=lead,
                new_status=LeadStatus.QUALIFIED,
            )


if __name__ == "__main__":
    unittest.main()
