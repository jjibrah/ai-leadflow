from datetime import datetime, timezone
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.models.enums import JobStatus
from app.repositories.follow_up_repository import FollowUpRepository


async def run_follow_up_job(ctx: dict, follow_up_job_id: str) -> None:
    try:
        parsed_job_id = UUID(follow_up_job_id)
    except ValueError:
        return

    async with AsyncSessionLocal() as db:
        follow_up = await FollowUpRepository.get_by_id(db, parsed_job_id)
        if follow_up is None or follow_up.status == JobStatus.COMPLETED:
            return

        follow_up.status = JobStatus.PROCESSING
        await db.commit()

        # Phase 8 will perform the actual follow-up action here.
        follow_up.status = JobStatus.COMPLETED
        follow_up.completed_at = datetime.now(timezone.utc)
        await db.commit()
