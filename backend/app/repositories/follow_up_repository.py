from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_job import FollowUpJob


class FollowUpRepository:
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        follow_up_job_id: UUID,
    ) -> FollowUpJob | None:
        result = await db.execute(
            select(FollowUpJob).where(FollowUpJob.id == follow_up_job_id)
        )
        return result.scalar_one_or_none()
