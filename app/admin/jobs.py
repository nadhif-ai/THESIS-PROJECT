import json
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from app.admin import store

_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="admin-job")


def list_jobs():
    with store.connection() as db:
        rows = db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return [
        dict(
            row,
            payload=json.loads(row["payload"]),
            result=json.loads(row["result"]) if row["result"] else None,
        )
        for row in rows
    ]


def create(kind, payload):
    identifier = uuid.uuid4().hex
    with store.connection() as db:
        db.execute(
            "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
            (
                identifier,
                kind,
                "queued",
                json.dumps(payload),
                None,
                None,
                store.now(),
                store.now(),
            ),
        )
    _worker.submit(run, identifier, kind, payload)
    return identifier


def run(identifier, kind, payload):
    with store.connection() as db:
        db.execute(
            "UPDATE jobs SET status='running',updated_at=? WHERE id=?",
            (store.now(), identifier),
        )
    try:
        if kind == "index":
            from app.admin.knowledge import index_version

            result = index_version(payload["version_id"])
        elif kind == "evaluate":
            from testing.evals.runner import run_evaluation

            result = run_evaluation(job_id=identifier, **payload)
        elif kind == "generate":
            from testing.evals.runner import generate_candidates

            result = generate_candidates(**payload)
        elif kind == "report":
            from testing.evals.runner import retry_report

            result = retry_report(payload["evaluation_id"])
        else:
            raise ValueError("Unknown job type.")
        with store.connection() as db:
            db.execute(
                "UPDATE jobs SET status='completed',result=?,updated_at=? WHERE id=?",
                (json.dumps(result), store.now(), identifier),
            )
    except Exception as error:
        logging.getLogger(__name__).exception(
            "Administration job %s failed", identifier
        )
        # Provider exception bodies may contain sensitive request details.
        message = (
            str(error)
            if isinstance(error, (ValueError, TimeoutError, FileNotFoundError))
            else f"{type(error).__name__}: job failed; inspect the application log before retrying."
        )
        with store.connection() as db:
            db.execute(
                "UPDATE jobs SET status='failed',error=?,updated_at=? WHERE id=?",
                (message, store.now(), identifier),
            )
