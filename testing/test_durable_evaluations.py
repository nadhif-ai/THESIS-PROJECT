from contextlib import nullcontext
from types import SimpleNamespace
import uuid

from app.admin import kb_store, store, durable_jobs
from app.backend.models import embedding_identity
from app.config.settings import get_settings


def seed():
    store.save_version(
        {
            "id": "active",
            "namespace": "kb-active",
            "status": "ready",
            "created_at": store.now(),
            "manifest": {
                "files": [],
                "embedding": embedding_identity(),
                "vector_index": get_settings().pinecone_index_name,
                "chunking": {"chunk_size": 1000, "chunk_overlap": 100},
            },
            "records": [
                {"id": "one", "document": "Synthetic evidence", "metadata": {}}
            ],
        }
    )
    store.publish("active")


def setup_runtime(monkeypatch):
    from app import dependencies
    from testing.evals import durable

    monkeypatch.setattr(
        durable, "Client", lambda **kwargs: SimpleNamespace(flush=lambda **kwargs: None)
    )
    monkeypatch.setattr(durable, "tracing_context", lambda **kwargs: nullcontext())
    monkeypatch.setattr(
        durable,
        "trace",
        lambda *args, **kwargs: nullcontext(
            SimpleNamespace(
                id=uuid.uuid4(), end=lambda **kwargs: None, get_url=lambda: None
            )
        ),
    )
    calls = []

    def answer(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            answer="Synthetic answer",
            error=None,
            retrieval_context=[{"text": "Synthetic evidence"}],
            usage={},
            latency_seconds=0.1,
        )

    monkeypatch.setattr(
        dependencies,
        "get_rag_chain",
        lambda: SimpleNamespace(prompt_fingerprint="fixed", run=answer),
    )
    return durable, calls


def test_answer_and_each_metric_checkpoint_survive_worker_recreation(
    pg_live, monkeypatch
):
    seed()
    module, calls = setup_runtime(monkeypatch)
    configuration = {
        "openrouter_model": "answer/fixed",
        "eval_model": "judge/fixed",
        "semantic_top_k": 3,
    }
    rows = [
        {
            "id": "q1",
            "question": "Synthetic question",
            "ground_truth": "Synthetic reference",
        }
    ]
    identifier = kb_store.create_evaluation(
        {"dataset": "legacy"}, {"configuration": configuration, "rows": rows}
    )

    class Metric:
        threshold = 0.7

        def __init__(self, name, error=False):
            self.__name__, self.error = name, error

        def measure(self, case):
            if self.error:
                raise RuntimeError("Synthetic judge failure")
            self.score, self.reason = 0.8, "Synthetic score"

        def is_successful(self):
            return True

    monkeypatch.setattr(
        module,
        "single_turn_metrics",
        lambda *args: [Metric("first"), Metric("second", True)],
    )
    assert durable_jobs.consume(identifier, 0)
    assert durable_jobs.consume(identifier, 1)
    assert len(calls) == 1
    assert kb_store.work(identifier)["checkpoint"]["phase"] == "scoring"
    store.set_settings({"openrouter_model": "changed", "semantic_top_k": 19})
    assert durable_jobs.consume(identifier, 2)
    assert len(store.job(identifier)["result"]["cases"]) == 0
    assert len(kb_store.work(identifier)["checkpoint"]["record"]["metrics"]) == 1
    assert durable_jobs.consume(identifier, 3)
    assert not durable_jobs.consume(identifier, 4)
    result = store.evaluation_result(identifier)
    assert result["averages"] == {"first": 0.8, "second": None}
    assert result["cases"][0]["metrics"][1]["error"] == "RuntimeError"
    assert result["namespace"] == "kb-active"
    assert calls[0]["model"] == "answer/fixed"
    assert calls[0]["top_k"] == 3
    assert len(calls) == 1
    assert store.job(identifier)["status"] == "completed"


def test_submission_captures_reference_rows_and_latest_active(pg_live, monkeypatch):
    seed()
    module, _ = setup_runtime(monkeypatch)
    rows = [{"id": "q1", "question": "Captured", "ground_truth": "Reference"}]
    monkeypatch.setattr(module, "load_cases", lambda *args: rows)
    monkeypatch.setattr(durable_jobs, "dispatch", lambda identifier: None)
    identifier = module.submit("legacy", 1)["job_id"]
    rows[0]["question"] = "Changed later"
    checkpoint = kb_store.work(identifier)["checkpoint"]
    assert checkpoint["rows"][0]["question"] == "Captured"
    assert checkpoint["snapshot"]["id"] == "active"


def test_prompt_snapshot_survives_save_restart_and_multiple_answer_steps(pg_live, monkeypatch):
    from app.admin import prompt_settings

    seed()
    module, calls = setup_runtime(monkeypatch)
    monkeypatch.setattr(module, "load_cases", lambda *args: [
        {"id": "first", "question": "First question", "ground_truth": "Reference"},
        {"id": "second", "question": "Second question", "ground_truth": "Reference"},
    ])
    monkeypatch.setattr(durable_jobs, "dispatch", lambda identifier: None)
    class Metric:
        __name__ = "Synthetic metric"
        threshold = 0.7

        def measure(self, case):
            self.score, self.reason = 0.8, "Synthetic score"

        def is_successful(self):
            return True

    monkeypatch.setattr(module, "single_turn_metrics", lambda *args: [Metric()])
    original = prompt_settings.save("Instruksi sebelum evaluasi.")
    identifier = module.submit("legacy", 2)["job_id"]
    checkpoint = kb_store.work(identifier)["checkpoint"]
    frozen = checkpoint["prompt_snapshot"]
    assert checkpoint["prompt_sha256"] == original["prompt_sha256"] == frozen["sha256"]
    prompt_settings.save("Instruksi setelah submit.")
    durable_jobs.consume(identifier, 0)
    durable_jobs.consume(identifier, 1)
    store.close_pool()
    prompt_settings.save("Instruksi setelah jawaban pertama.")
    for sequence in range(2, 6):
        durable_jobs.consume(identifier, sequence)
    result = store.evaluation_result(identifier)
    assert len(calls) == 2
    assert all(call["prompt_config"] == frozen for call in calls)
    assert result["prompt_sha256"] == original["prompt_sha256"]
    assert result["prompt_snapshot"] == frozen
    assert len(result["cases"]) == 2
    # Existing records remain readable without retroactively claiming a prompt snapshot.
    store.create_job_row("old-result", "evaluate", {})
    store.set_job_state("old-result", "completed", result={"id": "old-result", "prompt_sha256": "legacy-hash", "cases": []})
    assert store.evaluation_result("old-result") == {"id": "old-result", "prompt_sha256": "legacy-hash", "cases": []}


def test_conversation_resumes_saved_pairs_with_a_four_pair_limit(pg_live, monkeypatch):
    from deepeval.test_case import Turn

    seed()
    module, calls = setup_runtime(monkeypatch)
    monkeypatch.setattr(module, "judge", lambda model: object())

    class Simulator:
        def __init__(self, model_callback, **kwargs):
            self.callback = model_callback

        def simulate(self, conversational_goldens, max_user_simulations):
            assert max_user_simulations == 1
            turns = list(conversational_goldens[0].turns or [])
            user = Turn(role="user", content=f"Synthetic turn {len(turns) // 2 + 1}")
            turns.append(user)
            turns.append(self.callback(user.content, turns, "ignored-changing-id"))
            return [SimpleNamespace(turns=turns)]

    monkeypatch.setattr(module, "ConversationSimulator", Simulator)
    identifier = kb_store.create_evaluation(
        {"dataset": "conversations"},
        {
            "configuration": {
                "openrouter_model": "fixed",
                "eval_model": "fixed",
                "semantic_top_k": 3,
            },
            "rows": [
                {
                    "id": "q1",
                    "scenario": "Synthetic scenario",
                    "expected_outcome": "Synthetic reference",
                }
            ],
        },
    )
    durable_jobs.consume(identifier, 0)
    for index in range(4):
        durable_jobs.consume(identifier, index + 1)
        record = kb_store.work(identifier)["checkpoint"]["record"]
        assert len(record["turns"]) == (index + 1) * 2
    assert kb_store.work(identifier)["checkpoint"]["phase"] == "scoring"
    assert len(calls) == 4 and len({call["session_id"] for call in calls}) == 1
    assert all(call["namespace"] == "kb-active" for call in calls)


def test_reference_review_persists_without_writing_to_the_deployment(
    pg_live, monkeypatch, tmp_path
):
    import json
    from testing.evals import runner

    path = tmp_path / "references.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "a",
                    "question": "Question",
                    "ground_truth": "Reference",
                    "review_notes": "Guidance",
                    "review_status": "candidate",
                }
            ]
        )
    )
    monkeypatch.setattr(runner, "QA_DATASET", path)
    monkeypatch.setattr(
        runner, "QA_REVIEW", tmp_path / "read-only-missing-directory" / "review.json"
    )
    assert not runner.dataset_status("audited")["reviewed"]
    assert runner.mark_reviewed("audited")["reviewed"]
    assert not runner.QA_REVIEW.exists()
    path.write_text(path.read_text() + "\n")
    assert not runner.dataset_status("audited")["reviewed"]


def test_queue_failure_preserves_checkpoint_and_retry_uses_new_dispatch_key(
    pg_live, monkeypatch
):
    import vercel.queue.sync

    seed()
    identifier = kb_store.create_evaluation({"dataset": "legacy"}, {"rows": []})
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    with pg_live.admin_connection() as db:
        db.execute(
            "UPDATE chatbot.admin_work SET environment='production' WHERE job_id=%s",
            (identifier,),
        )

    class Queue:
        def send(self, *args, **kwargs):
            raise RuntimeError("Synthetic queue failure")

    monkeypatch.setattr(vercel.queue.sync, "QueueClient", Queue)
    import pytest

    with pytest.raises(RuntimeError, match="saved"):
        durable_jobs.dispatch(identifier)
    before = kb_store.work(identifier)
    assert before["status"] == "queued" and before["dispatch_error"]
    kb_store.retry(identifier)
    assert kb_store.work(identifier)["sequence"] == before["sequence"] + 1


def test_feedback_is_checkpointed_per_metric_and_retry_never_calls_a_judge(
    pg_live, monkeypatch
):
    from testing.evals import durable

    result = {
        "id": "saved",
        "dataset": "legacy",
        "project_id": "project",
        "deepeval_version": "synthetic",
        "cases": [
            {
                "id": "a",
                "trace_id": str(uuid.uuid4()),
                "metrics": [
                    {"name": "first", "score": 0.8},
                    {"name": "second", "score": 0.9},
                ],
            }
        ],
    }
    store.create_job_row("saved", "evaluate", {})
    store.set_job_state("saved", "completed", result=result)
    monkeypatch.setattr(durable_jobs, "dispatch", lambda identifier: None)
    monkeypatch.setattr(
        durable,
        "Client",
        lambda **kwargs: SimpleNamespace(
            read_project=lambda **kw: SimpleNamespace(
                url="https://example.invalid/experiment"
            )
        ),
    )
    sent = []
    monkeypatch.setattr(
        durable,
        "report_metric",
        lambda client, result, row, score: sent.append(score["name"]),
    )
    identifier = durable.submit_report("saved")["job_id"]
    assert durable_jobs.consume(identifier, 0)
    assert sent == ["first"]
    assert kb_store.work(identifier)["checkpoint"]["report_cursor"] == 1
    assert durable_jobs.consume(identifier, 1)
    assert sent == ["first", "second"]
    assert not durable_jobs.consume(identifier, 2)
    assert (
        store.evaluation_result("saved")["experiment_url"]
        == "https://example.invalid/experiment"
    )


def test_reporting_failure_preserves_scores_after_three_bounded_attempts(
    pg_live, monkeypatch
):
    from testing.evals import durable

    result = {
        "id": "saved",
        "dataset": "legacy",
        "project_id": "project",
        "cases": [{"id": "a", "metrics": [{"name": "score", "score": 0.8}]}],
    }
    store.create_job_row("saved", "evaluate", {})
    store.set_job_state("saved", "completed", result=result)
    monkeypatch.setattr(durable_jobs, "dispatch", lambda identifier: None)
    monkeypatch.setattr(durable, "Client", lambda **kwargs: object())
    calls = []

    def unavailable(*args):
        calls.append(1)
        raise RuntimeError("Synthetic reporting outage")

    monkeypatch.setattr(durable, "report_metric", unavailable)
    identifier = durable.submit_report("saved")["job_id"]
    assert durable_jobs.consume(identifier, 0)
    assert durable_jobs.consume(identifier, 1)
    assert not durable_jobs.consume(identifier, 2)
    assert len(calls) == 3
    assert store.evaluation_result("saved")["cases"][0]["metrics"][0]["score"] == 0.8
    assert store.evaluation_result("saved")["reporting_error"] == "RuntimeError"
