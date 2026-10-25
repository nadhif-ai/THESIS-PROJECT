"""Private, request-bound Vercel consumer; PostgreSQL owns ordering and delivery state."""

import hashlib
import logging
import os

import anyio
from vercel.queue import DuplicateIdempotencyKeyError, QueueClient, RetryAfter, subscribe

from app.admin import store

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TOPIC = "whatsapp-replies"


def enabled():
    return os.getenv("VERCEL") == "1"


async def notify(session, message_id):
    key = hashlib.sha256((session + ":" + message_id).encode()).hexdigest()
    try:
        await QueueClient().send(TOPIC, {"session": session, "message_id": message_id}, idempotency_key=key)
    except DuplicateIdempotencyKeyError:
        pass


def consume(payload):
    from app.config.settings import get_settings
    from app.integrations import waha

    session, message_id = payload["session"], payload["message_id"]
    if session != get_settings().waha_session:
        raise ValueError("Queue session does not match this deployment.")
    item = hashlib.sha256(message_id.encode()).hexdigest()[:12]
    row = store.claim_inbox(session, message_id)
    if row:
        logger.info("WhatsApp phase=claimed item=%s execution=vercel_queue", item)
        waha.process(dict(row))
    state = store.get_inbox(session, message_id)
    if state is None or state["status"] in ("queued", "generating", "sending"):
        # Another invocation owns this chat, or an interrupted generation needs its lease to expire.
        logger.info("WhatsApp phase=deferred item=%s status=%s retry_seconds=10",
                    item, state["status"] if state else "missing")
        raise RetryAfter(10)
    logger.info("WhatsApp phase=finished item=%s status=%s", item, state["status"])


@subscribe(topic=TOPIC, consumer_group="whatsapp-replies-v1", retry_after=10, max_concurrency=4, max_attempts=100)
async def reply(payload: dict[str, str]) -> None:
    # Keep the event loop available for the SDK's processing-lease renewal.
    await anyio.to_thread.run_sync(consume, payload)
