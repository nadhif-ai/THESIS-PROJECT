"""Progress persists across polling without running model or WhatsApp APIs."""

import json
import uuid
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from app.admin import jobs, store
from app.config.settings import get_settings


@pytest.fixture
def workspace(tmp_path, monkeypatch, pg_live):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ADMIN_PASSWORD", "offline-test")
    get_settings.cache_clear()
    monkeypatch.setattr(jobs, "_worker", SimpleNamespace(submit=lambda *args: None))
    yield tmp_path
    get_settings.cache_clear()


def test_existing_job_results_are_preserved_on_reads(pg_live):
    store.create_job_row("old", "evaluate", {})
    store.set_job_state("old", "completed", result={"cases": []})
    for _ in range(2):
        old = jobs.list_jobs()[0]
        assert old["result"] == {"cases": []}
        assert old["progress"] == {}


def test_evaluation_reports_actual_cases_and_metric_errors(workspace, monkeypatch):
    from app import dependencies
    from testing.evals import runner

    item = {
        "id": "offline",
        "namespace": "offline",
        "status": "ready",
        "created_at": store.now(),
        "manifest": {},
        "records": [],
        "error": None,
    }
    store.save_version(item)
    rows = [
        {
            "id": str(index),
            "question": f"Offline case {index}",
            "ground_truth": "Offline reference",
        }
        for index in range(2)
    ]
    monkeypatch.setattr(runner, "load_cases", lambda *args: rows)
    monkeypatch.setattr(
        runner, "Client", lambda: SimpleNamespace(flush=lambda **kwargs: None)
    )
    monkeypatch.setattr(
        runner,
        "_sync_dataset",
        lambda *args: (_ for _ in ()).throw(ValueError("Reporting offline")),
    )
    monkeypatch.setattr(runner, "tracing_context", lambda **kwargs: nullcontext())
    monkeypatch.setattr(
        runner,
        "trace",
        lambda *args, **kwargs: nullcontext(
            SimpleNamespace(
                id=uuid.uuid4(), end=lambda **kwargs: None, get_url=lambda: None
            )
        ),
    )
    monkeypatch.setattr(
        runner,
        "retry_report",
        lambda identifier: json.loads(
            (workspace / "evaluations" / identifier / "results.json").read_text()
        ),
    )
    monkeypatch.setattr(
        dependencies,
        "get_rag_chain",
        lambda: SimpleNamespace(
            prompt_fingerprint="offline",
            run=lambda **kwargs: SimpleNamespace(
                answer="Offline answer",
                error=None,
                retrieval_context=[],
                usage={},
                latency_seconds=0,
            ),
        ),
    )
    observed = []

    class Metric:
        __name__ = "Offline metric"
        threshold = 0.7

        def measure(self, case):
            observed.append(jobs.list_jobs()[0]["progress"])
            if case.input.endswith("1"):
                raise ValueError("Offline scoring failure")
            self.score, self.reason = 0.5, "Offline low quality result"

        def is_successful(self):
            return False

    monkeypatch.setattr(runner, "single_turn_metrics", lambda *args: [Metric()])
    payload = {"version_id": "offline", "dataset": "legacy", "limit": 10}
    identifier = jobs.create("evaluate", payload)
    jobs.run(identifier, "evaluate", payload)
    job = jobs.list_jobs()[0]
    assert job["status"] == "completed"
    assert job["progress"]["completed"] == job["progress"]["total"] == 2
    assert job["progress"]["errors"] == 1
    assert job["progress"]["phase"] == "completed"
    assert job["progress"]["case_label"] is None
    assert [state["completed"] for state in observed] == [0, 1]
    assert all(
        state["phase"] == "scoring" and state["metrics_completed"] == 0
        for state in observed
    )
    assert job["result"]["cases"][0]["metrics"][0]["passed"] is False
    assert job["result"]["cases"][1]["metrics"][0]["score"] is None


def test_failed_job_preserves_observed_progress(workspace, monkeypatch):
    from app.admin import knowledge

    identifier = jobs.create("index", {"version_id": "offline"})

    def failure(version_id):
        jobs.update_progress(identifier, completed=1, total=3)
        raise RuntimeError("private provider response")

    monkeypatch.setattr(knowledge, "index_version", failure)
    jobs.run(identifier, "index", {"version_id": "offline"})
    job = jobs.list_jobs()[0]
    assert job["status"] == job["progress"]["phase"] == "failed"
    assert job["progress"]["completed"] == 1
    assert "private provider response" not in job["error"]


def test_waha_status_reports_observed_queue_and_times(workspace, monkeypatch):
    from app.integrations import waha

    monkeypatch.setenv("WHATSAPP_PROVIDER", "waha")
    monkeypatch.setenv("WAHA_API_KEY", "offline-key")
    monkeypatch.setenv("WAHA_WEBHOOK_SECRET", "offline-secret")
    monkeypatch.setenv(
        "WAHA_WEBHOOK_URL", "https://callback.example.test/chat/waha/webhook"
    )
    get_settings.cache_clear()
    waha.initialize()
    monkeypatch.setattr(
        waha,
        "api",
        lambda *args, **kwargs: {"status": "STARTING", "engine": {"engine": "GOWS"}},
    )
    message = waha.Message.model_validate(
        {"id": "offline-message", "from": "123@c.us", "body": "Offline message"}
    )
    waha.enqueue(message)
    observed = waha.status()
    assert observed["session_status"] == "STARTING"
    assert observed["queue"] == {"queued": 1}
    assert observed["last_received_at"]
    assert observed["last_sent_at"] is None
    assert observed["last_ack_at"] is None
    assert observed["credentials_configured"] and observed["webhook_configured"]
    assert "offline-key" not in json.dumps(observed)

    def unreachable(*args, **kwargs):
        raise ValueError("Private server error")

    monkeypatch.setattr(waha, "api", unreachable)
    unavailable = waha.status()
    assert unavailable["session_status"] == "unreachable"
    assert unavailable["checked_at"]
    assert unavailable["queue"] == {"queued": 1}
