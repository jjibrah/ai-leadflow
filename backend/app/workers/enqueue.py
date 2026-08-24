from datetime import datetime
from uuid import UUID

from arq.connections import ArqRedis


async def enqueue_enquiry_processing(
    redis: ArqRedis,
    enquiry_id: UUID,
):
    return await redis.enqueue_job(
        "process_enquiry_job",
        str(enquiry_id),
        _job_id=f"process-enquiry:{enquiry_id}",
    )


async def enqueue_follow_up(
    redis: ArqRedis,
    follow_up_job_id: UUID,
    scheduled_for: datetime,
):
    return await redis.enqueue_job(
        "run_follow_up_job",
        str(follow_up_job_id),
        _defer_until=scheduled_for,
        _job_id=f"follow-up:{follow_up_job_id}",
    )
