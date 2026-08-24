import asyncio
from types import SimpleNamespace

from app.services.ai.exceptions import AIServiceError
from app.services.ai.service import create_ai_service


async def main() -> None:
    enquiry = SimpleNamespace(
        name="John Doe",
        email="john@acmelogistics.com",
        company="Acme Logistics",
        message="We need an ERP solution for our logistics company.",
    )

    try:
        result = await create_ai_service().process_enquiry(enquiry)
    except AIServiceError as exc:
        print(f"AI processing failed safely: {exc}")
        cause = exc.__cause__

        if cause is not None:
            print(f"Provider error type: {type(cause).__name__}")

            status_code = getattr(cause, "status_code", None)
            error_code = getattr(cause, "code", None)

            if status_code is not None:
                print(f"Provider HTTP status: {status_code}")

            if error_code is not None:
                print(f"Provider error code: {error_code}")

        raise SystemExit(1) from None

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
