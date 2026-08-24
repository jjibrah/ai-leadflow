import hashlib
import hmac
import time

from fastapi import HTTPException, status

from app.core.config import settings


class SignatureService:

    MAX_TIMESTAMP_DIFFERENCE = 300

    # Signature Verification Service
    @staticmethod
    def validate_timestamp(timestamp: str) -> None:
        try:
            timestamp_value = int(timestamp)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook timestamp.",
            )

        current_time = int(time.time())

        if abs(current_time - timestamp_value) > SignatureService.MAX_TIMESTAMP_DIFFERENCE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook timestamp expired.",
            )


    #HMAC Verification
    @staticmethod
    def verify_signature(
        raw_body: bytes,
        timestamp: str,
        received_signature: str,
    ) -> None:

        signing_payload = (
            timestamp.encode("utf-8")
            + b"."
            + raw_body
        )

        expected_signature = hmac.new(
            settings.WEBHOOK_SECRET.encode("utf-8"),
            signing_payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            expected_signature,
            received_signature,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )