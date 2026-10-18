from copy import deepcopy
from types import SimpleNamespace

import pytest

from testing.evals.calculations import (
    judge_calculation, passage_key, question_key, retrieval_manifest, retrieval_metrics,
)


def sample():
    contexts = [
        {"text": "Synthetic relevant evidence", "metadata": {"source": "one.txt"}},
        {"text": "Synthetic unrelated evidence", "metadata": {"source": "two.txt"}},
    ]
    manifest = retrieval_manifest(contexts)
    row = {"question": "Synthetic question"}
    row["retrieval_annotations"] = {
        "snapshot_sha256": manifest["snapshot_sha256"],
        "question_sha256": question_key(row["question"]),
        "facts": [{"id": f"f{i}", "text": f"Synthetic fact {i}"} for i in range(3)],
        "passages": {
            passage_key(contexts[0]): {"relevant": True, "fact_ids": ["f0", "f1", "f1"]},
            passage_key(contexts[1]): {"relevant": False, "fact_ids": []},
        },
    }
    return row, {"retrieval_context": contexts}, {"runtime_top_k": 3, "retrieval_manifest": manifest}


def test_precision_uses_requested_k_and_coverage_counts_distinct_facts():
    metrics = retrieval_metrics(*sample())
    assert metrics[0]["score"] == pytest.approx(1 / 3)
    assert metrics[1]["score"] == pytest.approx(2 / 3)
    assert metrics[0]["calculation"]["returned"] == 2
    assert metrics[1]["calculation"]["numerator"] == 2
    assert all(metric["passed"] is None for metric in metrics)


@pytest.mark.parametrize("change", ["missing", "stale_question", "stale_snapshot", "missing_label", "unknown_fact", "contradictory_label", "duplicate_fact", "unknown_passage", "invalid_k"])
def test_missing_or_invalid_annotations_do_not_become_zero_scores(change):
    row, record, result = sample()
    annotation = row["retrieval_annotations"]
    key = passage_key(record["retrieval_context"][0])
    if change == "missing": row.pop("retrieval_annotations")
    elif change == "stale_question": row["question"] = "Changed question"
    elif change == "stale_snapshot": annotation["snapshot_sha256"] = "stale"
    elif change == "missing_label": annotation["passages"].pop(key)
    elif change == "unknown_fact": annotation["passages"][key]["fact_ids"] = ["unknown"]
    elif change == "contradictory_label": annotation["passages"][key]["relevant"] = False
    elif change == "duplicate_fact": annotation["facts"].append(deepcopy(annotation["facts"][0]))
    elif change == "unknown_passage": annotation["passages"]["unknown"] = {"relevant": False, "fact_ids": []}
    elif change == "invalid_k": result["runtime_top_k"] = 0
    metrics = retrieval_metrics(row, record, result)
    assert all(m["score"] is None and m["status"] == "unavailable" and "error" not in m for m in metrics)


def test_manifest_binds_text_and_source_but_not_record_order():
    _, record, _ = sample()
    contexts = record["retrieval_context"]
    assert retrieval_manifest(contexts) == retrieval_manifest(list(reversed(contexts)))
    changed = deepcopy(contexts)
    changed[0]["metadata"]["source"] = "different.txt"
    assert retrieval_manifest(contexts) != retrieval_manifest(changed)


def test_zero_retrieval_is_scored_only_with_valid_annotations():
    row, record, result = sample()
    record["retrieval_context"] = []
    assert [m["score"] for m in retrieval_metrics(row, record, result)] == [0, 0]


@pytest.mark.parametrize("name", ["Faithfulness", "Answer Relevancy"])
def test_judge_breakdown_exposes_borderline_policy(name):
    metric = SimpleNamespace(__name__=name, score=2 / 3,
        verdicts=[{"verdict": v} for v in ["yes", "borderline", "no"]],
        claims=["a", "b", "c"], statements=["a", "b", "c"])
    calculation = judge_calculation(metric)
    assert calculation["numerator"] == 2
    assert calculation["denominator"] == 3
    assert calculation["items"][1]["counted"]
    metric.score = 0.99
    assert judge_calculation(metric) is None
    metric.verdicts, metric.score = [None, {"verdict": "yes"}], 1
    assert judge_calculation(metric)["denominator"] == 1
    assert judge_calculation(metric)["items"][0]["label"] == "b"


def test_judge_empty_convention_does_not_invent_claims():
    metric = SimpleNamespace(__name__="Faithfulness", score=1, verdicts=[])
    calculation = judge_calculation(metric)
    assert calculation["denominator"] == 0
    assert calculation["empty_score"] == 1
    assert calculation["items"] == []


def test_ranked_context_precision_is_not_unweighted_precision():
    metric = SimpleNamespace(__name__="Contextual Precision", score=(1 + 2 / 3) / 2,
        verdicts=[{"verdict": v} for v in ["yes", "no", "yes"]])
    calculation = judge_calculation(metric)
    assert calculation["numerator"] == pytest.approx(1 + 2 / 3)
    assert calculation["denominator"] == 2
