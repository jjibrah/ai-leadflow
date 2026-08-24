from fastapi import APIRouter, Header, Request, status

from app.services.signature_service import SignatureService


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)
@router.post(
    "/enquiries",
    status_code=status.HTTP_200_OK,
)
async def receive_enquiry_webhook(
    request: Request,
    x_webhook_event_id: str = Header(...),
    x_webhook_timestamp: str = Header(...),
    x_webhook_signature: str = Header(...),
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

    return {
        "status": "verified"
    }