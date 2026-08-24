from arq.worker import func

from app.services.ai.service import create_ai_service
from app.workers.dependencies import redis_settings
from app.workers.jobs.follow_up import run_follow_up_job
from app.workers.jobs.process_enquiry import MAX_TRIES, process_enquiry_job


async def startup(ctx: dict) -> None:
    ctx["ai_service"] = create_ai_service()


class WorkerSettings:
    functions = [
        func(
            process_enquiry_job,
            max_tries=MAX_TRIES,
            timeout=60,
            keep_result=60,
        ),
        func(run_follow_up_job, max_tries=1, timeout=60),
    ]
    redis_settings = redis_settings
    on_startup = startup
    max_jobs = 10
