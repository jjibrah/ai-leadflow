import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.workers.enqueue import enqueue_enquiry_processing


class EnqueueTests(unittest.IsolatedAsyncioTestCase):
    async def test_enquiry_job_uses_stable_unique_id(self):
        redis = AsyncMock()
        enquiry_id = uuid4()

        await enqueue_enquiry_processing(redis, enquiry_id)

        redis.enqueue_job.assert_awaited_once_with(
            "process_enquiry_job",
            str(enquiry_id),
            _job_id=f"process-enquiry:{enquiry_id}",
        )


if __name__ == "__main__":
    unittest.main()
