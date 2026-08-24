from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_event import WebhookEvent


class WebhookRepository:

    @staticmethod
    async def get_by_event_id(
        db: AsyncSession,
        event_id: str,
    ) -> WebhookEvent | None:

        result = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.event_id == event_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        webhook_event: WebhookEvent,
    ) -> WebhookEvent:

        db.add(webhook_event)

        await db.flush()

        return webhook_event
