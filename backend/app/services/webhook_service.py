import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_event import WebhookEvent
from app.repositories.webhook_repository import WebhookRepository
from app.schemas.enquiry import EnquiryCreate
from app.services.enquiry_service import EnquiryService


class WebhookService:

    @staticmethod
    async def process_enquiry_webhook(
        db: AsyncSession,
        *,
        event_id: str,
        raw_body: bytes,
    ):
        existing_event = await WebhookRepository.get_by_event_id(
            db,
            event_id,
        )

        if existing_event:
            return {
                "status": "already_processed",
                "message": None,
            }

        payload_hash = hashlib.sha256(raw_body).hexdigest()

        try:
            payload_dict = json.loads(raw_body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON payload.",
            )

        try:
            enquiry_data = EnquiryCreate.model_validate(payload_dict)
        except ValidationError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid enquiry payload.",
            )

        webhook_event = WebhookEvent(
            event_id=event_id,
            payload_hash=payload_hash,
            status="received",
            received_at=datetime.now(timezone.utc),
        )

        try:
            await WebhookRepository.create(
                db,
                webhook_event,
            )

            enquiry = await EnquiryService.create_enquiry(
                db=db,
                data=enquiry_data,
            )

            webhook_event.enquiry_id = enquiry.id
            webhook_event.status = "processed"
            webhook_event.processed_at = datetime.now(timezone.utc)

            await db.commit()

            return {
                "status": "accepted",
                "message": "Webhook processed successfully.",
            }

        except IntegrityError:
            await db.rollback()

            existing_event = await WebhookRepository.get_by_event_id(
                db,
                event_id,
            )

            if existing_event:
                return {
                    "status": "already_processed",
                    "message": None,
                }

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process webhook.",
            )

        except Exception:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process webhook.",
            )
