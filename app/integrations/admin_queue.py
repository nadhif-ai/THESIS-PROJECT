"""Private Vercel subscriber for resumable indexing and evaluation steps."""

import os
import hashlib

import anyio
from vercel.queue import subscribe

from app.admin import durable_jobs, kb_store

TOPIC = (
    "admin-work-production"
    if os.getenv("VERCEL_ENV") == "production"
    else "admin-work-preview"
)
CLEANUP_TOPIC = TOPIC + "-cleanup"


def schedule_cleanup(identifier, page=0):
    if os.getenv("VERCEL") != "1":
        return
    from vercel.queue.sync import QueueClient
    from vercel.queue import DuplicateIdempotencyKeyError

    try:
        QueueClient().send(
            CLEANUP_TOPIC,
            {"id": identifier, "page": page, "environment": kb_store.environment()},
            idempotency_key=hashlib.sha256(
                f"cleanup:{identifier}:{page}".encode()
            ).hexdigest(),
            delay=86400 if page == 0 else 1,
            retention=604800,
        )
    except DuplicateIdempotencyKeyError:
        pass


@subscribe(
    topic=TOPIC,
    consumer_group="admin-steps-v1",
    retry_after=10,
    max_concurrency=2,
    max_attempts=100,
)
async def administration(payload: dict[str, object]) -> None:
    if payload.get("environment") != kb_store.environment():
        return
    more = await anyio.to_thread.run_sync(
        durable_jobs.consume, payload["job_id"], payload["sequence"]
    )
    if more:
        # On redelivery of an old step, dispatch the current checkpoint using its stable key.
        await anyio.to_thread.run_sync(durable_jobs.dispatch, payload["job_id"])


@subscribe(
    topic=CLEANUP_TOPIC,
    consumer_group="knowledge-cleanup-v1",
    retry_after=30,
    max_concurrency=1,
    max_attempts=100,
)
async def cleanup(payload: dict[str, object]) -> None:
    if payload.get("environment") != kb_store.environment():
        return
    from app.admin.global_knowledge import cleanup as collect

    if await anyio.to_thread.run_sync(collect):
        await anyio.to_thread.run_sync(
            schedule_cleanup, payload["id"], payload["page"] + 1
        )
