import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from app.admin import store

_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="admin-job")


def list_jobs():
    return store.list_job_rows()


def create(kind, payload):
    identifier = uuid.uuid4().hex
    store.create_job_row(identifier, kind, payload)
    _worker.submit(run, identifier, kind, payload)
    return identifier


def update_progress(identifier, **fields):
    store.merge_job_progress(identifier, fields)


def run(identifier, kind, payload):
    store.set_job_state(identifier, "running")
    update_progress(identifier, phase="preparing", started_at=store.now())
    try:
        if kind == "index":
            from app.admin.knowledge import index_version

            update_progress(identifier, phase="indexing")
            result = index_version(payload["version_id"])
        elif kind == "evaluate":
            from testing.evals.runner import run_evaluation

            result = run_evaluation(job_id=identifier, **payload)
        elif kind == "generate":
            from testing.evals.runner import generate_candidates

            update_progress(identifier, phase="generating")
            result = generate_candidates(**payload)
        elif kind == "report":
            from testing.evals.runner import retry_report

            update_progress(identifier, phase="reporting")
            result = retry_report(payload["evaluation_id"])
        else:
            raise ValueError("Unknown job type.")
        store.set_job_state(identifier, "completed", result=result)
        update_progress(
            identifier, phase="completed", case_id=None, case_label=None, metric=None
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
        store.set_job_state(identifier, "failed", error=message)
        update_progress(identifier, phase="failed")
