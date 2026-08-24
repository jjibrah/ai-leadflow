import unittest
from unittest.mock import patch
from uuid import uuid4

from app.api.routes.enquiries import create_enquiry
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus
from app.schemas.enquiry import EnquiryCreate


class RecordingDatabase:
    def __init__(self, events):
        self.events = events

    async def commit(self):
        self.events.append("commit")

    async def rollback(self):
        self.events.append("rollback")


class RecordingRedis:
    def __init__(self, events):
        self.events = events

    async def enqueue_job(self, *args, **kwargs):
        self.events.append("enqueue")


class EnquiryRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_commits_pending_enquiry_before_enqueue(self):
        events = []
        db = RecordingDatabase(events)
        redis = RecordingRedis(events)
        enquiry = Enquiry(
            id=uuid4(),
            name="John Doe",
            email="john@example.com",
            company=None,
            message="We need help selecting an ERP system.",
            source="website",
            status=EnquiryStatus.RECEIVED,
        )
        payload = EnquiryCreate(
            name=enquiry.name,
            email=enquiry.email,
            message=enquiry.message,
        )

        with (
            patch(
                "app.api.routes.enquiries.EnquiryService.create_enquiry",
                return_value=enquiry,
            ),
            patch(
                "app.api.routes.enquiries.settings.BACKGROUND_JOBS_ENABLED",
                True,
            ),
        ):
            response = await create_enquiry(payload, db, redis)

        self.assertEqual(events, ["commit", "enqueue"])
        self.assertEqual(enquiry.status, EnquiryStatus.PENDING_PROCESSING)
        self.assertEqual(response.status, "pending_processing")


if __name__ == "__main__":
    unittest.main()
