from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.webhook import WebhookResponse
from app.services.signature_service import SignatureService
from app.services.webhook_service import WebhookService


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post(
    "/enquiries",
    response_model=WebhookResponse,
    response_model_exclude_none=True,
)
async def receive_enquiry_webhook(
    request: Request,
    response: Response,
    x_webhook_event_id: str = Header(..., min_length=1, max_length=255),
    x_webhook_timestamp: str = Header(...),
    x_webhook_signature: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()

    SignatureService.validate_timestamp(
        x_webhook_timestamp
    )

    SignatureService.verify_signature(
        raw_body=raw_body,
        timestamp=x_webhook_timestamp,
        received_signature=x_webhook_signature,
    )

    result = await WebhookService.process_enquiry_webhook(
        db=db,
        event_id=x_webhook_event_id,
        raw_body=raw_body,
    )

    if result["status"] == "already_processed":
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED

    return result
