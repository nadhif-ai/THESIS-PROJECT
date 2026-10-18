"""One lease per bounded step. PostgreSQL is authoritative across queue redelivery."""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from app.admin import kb_store, store

logger = logging.getLogger(__name__)
_local = ThreadPoolExecutor(max_workers=1, thread_name_prefix="admin-checkpoints")


def dispatch(identifier):
    if os.getenv("VERCEL") != "1":
        _local.submit(_run_local, identifier)
        return
    from vercel.queue.sync import QueueClient
    from vercel.queue import DuplicateIdempotencyKeyError
    from app.integrations.admin_queue import TOPIC

    row = kb_store.work(identifier)
    if not row or row["status"] not in ("queued", "running"):
        return
    try:
        QueueClient().send(
            TOPIC,
            {
                "job_id": identifier,
                "sequence": row["sequence"],
                "environment": row["environment"],
            },
            idempotency_key=f"{identifier}:{row['sequence']}",
            retention=604800,
            delay=min(60, row["checkpoint"].get("report_attempts", 0) * 10),
        )
    except DuplicateIdempotencyKeyError:
        return
    except Exception:
        with store._connection("execution") as db:
            db.execute(
                "UPDATE chatbot.admin_work SET dispatch_error='Queue publication failed; resume this job.' WHERE job_id=%s",
                (identifier,),
            )
        raise RuntimeError(
            "Queue publication failed. The job is saved; use Resume to dispatch it again."
        ) from None


def consume(identifier, sequence):
    row = kb_store.work(identifier)
    if not row or row["status"] not in ("queued", "running"):
        return False
    if row["environment"] != kb_store.environment():
        raise ValueError("Job belongs to a different deployment environment.")
    if sequence != row["sequence"]:
        return True
    claimed = kb_store.claim(identifier, sequence)
    if not claimed:
        raise RuntimeError("Another execution owns this step; retry after its lease.")
    try:
        logger.info(
            "Administration execution=%s job=%s kind=%s sequence=%s phase=%s",
            "vercel_queue" if os.getenv("VERCEL") == "1" else "local_worker",
            identifier,
            row["kind"],
            sequence,
            claimed["checkpoint"].get("phase"),
        )
        if row["kind"] == "sync":
            from app.admin.global_knowledge import sync_step

            step = sync_step
        else:
            from testing.evals.durable import evaluation_step

            step = evaluation_step
        state, progress, result, done = step(
            identifier, claimed["checkpoint"], claimed["lease_token"]
        )
        kb_store.checkpoint(
            identifier,
            claimed["lease_token"],
            state,
            progress,
            result=result,
            done=done,
        )
        return not done
    except Exception as error:
        logger.warning(
            "Administration step failed kind=%s phase=%s error=%s",
            row["kind"],
            claimed["checkpoint"].get("phase"),
            type(error).__name__,
        )
        kb_store.release_error(
            identifier,
            claimed["lease_token"],
            f"{type(error).__name__}: step failed; resume from the saved checkpoint. Active knowledge has not been removed.",
        )
        raise


def _run_local(identifier):
    while True:
        row = kb_store.work(identifier)
        if not row or row["status"] not in ("queued", "running"):
            return
        try:
            if not consume(identifier, row["sequence"]):
                return
        except Exception:
            time.sleep(3)


def resume(identifier):
    kb_store.retry(identifier)
    dispatch(identifier)


def stop():
    _local.shutdown(wait=True)
