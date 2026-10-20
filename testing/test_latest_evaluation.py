"""Dashboard evaluation summaries use saved QA evidence, never legacy baselines."""

import time

from app.admin import store


def test_overview_selects_latest_completed_qa_without_case_payloads(pg_live):
    store.create_session("overview-test", time.time() + 60, "csrf")

    def overview():
        return store.admin_snapshot("overview-test", time.time(), "overview")["data"]

    assert overview().get("latest_evaluation") is None
    result = {
        "id": "qa-result", "dataset": "audited", "knowledge_version": "older",
        "runtime_top_k": 5, "completed_at": "2026-10-20T10:00:00+00:00",
        "averages": {"Faithfulness": 0, "Contextual Recall": None},
        "cases": [{"id": "1", "answer": "private case text", "metrics": [
            {"name": "Faithfulness", "score": 0},
            {"name": "Contextual Recall", "score": None},
        ]}],
    }
    store.create_job_row("qa", "evaluate", {})
    store.set_job_state("qa", "completed", result=result)
    # Newer conversation runs, partial runs and unrelated jobs must not replace QA.
    for index in range(12):
        identifier = f"newer{index}"
        store.create_job_row(identifier, "evaluate", {})
        store.set_job_state(identifier, "completed", result=result | {"dataset": "conversations"})
    store.create_job_row("partial", "evaluate", {})
    store.set_job_state("partial", "failed", result=result)
    summary = overview()["latest_evaluation"]
    assert summary["job_id"] == "qa"
    assert summary["case_count"] == 1
    assert summary["averages"] == result["averages"]
    assert summary["scored_cases"] == {"Faithfulness": 1, "Contextual Recall": 0}
    assert summary["knowledge_version"] == "older" and summary["runtime_top_k"] == 5
    assert "cases" not in summary
    store.create_job_row("newqa", "evaluate", {})
    store.set_job_state("newqa", "completed", result=result | {"dataset": "legacy"})
    assert overview()["latest_evaluation"]["job_id"] == "newqa"
    # Resuming an older run can finish after a newer run; report retries cannot reorder it.
    store.set_job_state("qa", "completed", result=result | {"completed_at": "2026-10-20T11:00:00Z"})
    assert overview()["latest_evaluation"]["job_id"] == "qa"
