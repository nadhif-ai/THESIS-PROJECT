"""Reproducible retrieval arithmetic and saved judge evidence, without model calls."""

import hashlib
import json
import math

RECIPE = "rag-four-metrics-v1"
ANNOTATED_RECIPE = "chunking-fact-coverage-v1"
RETRIEVAL_NAMES = ("Precision@k", "Fact Coverage@k")


def passage_key(record):
    value = {
        "source": record.get("metadata", {}).get("source", ""),
        "text": record.get("text", record.get("document", "")),
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def retrieval_manifest(records):
    keys = sorted({passage_key(record) for record in records})
    return {
        "snapshot_sha256": hashlib.sha256("\n".join(keys).encode()).hexdigest(),
        "passage_keys": keys,
    }


def question_key(question):
    return hashlib.sha256(question.encode()).hexdigest()


def retrieval_metrics(row, record, result):
    def unavailable(reason):
        return [
            {"name": name, "score": None, "reason": reason, "passed": None,
             "status": "unavailable", "method": "annotated_retrieval"}
            for name in RETRIEVAL_NAMES
        ]

    annotation = row.get("retrieval_annotations")
    if not annotation:
        return unavailable("Offline passage labels and reference facts have not been supplied for this case.")
    if not isinstance(annotation, dict):
        return unavailable("Retrieval annotations must be an object.")
    manifest = result.get("retrieval_manifest", {})
    if (not isinstance(manifest, dict) or not manifest.get("snapshot_sha256")
            or annotation.get("snapshot_sha256") != manifest.get("snapshot_sha256")
            or annotation.get("question_sha256") != question_key(row["question"])):
        return unavailable("Annotations do not match the captured question and passage snapshot. Re-annotate this configuration.")
    facts = annotation.get("facts")
    labels = annotation.get("passages")
    if (not isinstance(facts, list) or not facts or not isinstance(labels, dict)
            or any(not isinstance(f, dict) or not isinstance(f.get("id"), str)
                   or not f["id"].strip() or not isinstance(f.get("text"), str)
                   or not f["text"].strip() for f in facts)):
        return unavailable("Annotations require a nonempty list of named reference facts and passage labels.")
    fact_ids = {fact["id"] for fact in facts}
    if len(fact_ids) != len(facts):
        return unavailable("Reference fact IDs must be unique.")
    for key, label in labels.items():
        if (key not in manifest.get("passage_keys", []) or not isinstance(label, dict)
                or type(label.get("relevant")) is not bool
                or not isinstance(label.get("fact_ids"), list)
                or any(not isinstance(f, str) or f not in fact_ids for f in label["fact_ids"])
                or (not label["relevant"] and label["fact_ids"])):
            return unavailable("A passage label has an unknown passage, invalid relevance verdict, or invalid fact mapping.")
    k = result.get("runtime_top_k")
    if type(k) is not int or k < 1:
        return unavailable("A positive captured top-k is required.")
    contexts = record.get("retrieval_context", [])[:k]
    keys = [passage_key(context) for context in contexts]
    if len(set(keys)) != len(keys) or any(key not in labels for key in keys):
        return unavailable("Every returned passage needs a unique, explicit relevance label; missing labels are not treated as irrelevant.")
    relevant = sum(labels[key]["relevant"] for key in keys)
    covered = {fact for key in keys for fact in labels[key]["fact_ids"]}
    counts = (
        (relevant, k, "P@k = Σ rᵢ / k", [
            {"label": f"Rank {i}: {context.get('metadata', {}).get('source', 'passage')}",
             "counted": labels[key]["relevant"], "detail": key}
            for i, (key, context) in enumerate(zip(keys, contexts), 1)
        ]),
        (len(covered), len(facts), "FC@k = |covered reference facts| / |all reference facts|", [
            {"label": fact["text"], "counted": fact["id"] in covered, "detail": fact["id"]}
            for fact in facts
        ]),
    )
    return [
        {"name": name, "score": numerator / denominator, "passed": None,
         "method": "annotated_retrieval", "status": "scored",
         "reason": "Deterministic calculation from offline annotations. No LLM relevance judgement or source-filename proxy is used.",
         "calculation": {"formula": formula, "numerator": numerator,
                         "denominator": denominator, "k": k,
                         "returned": len(contexts), "items": items}}
        for name, (numerator, denominator, formula, items) in zip(RETRIEVAL_NAMES, counts)
    ]


def judge_calculation(metric, case=None):
    name = metric.__name__
    if name not in ("Faithfulness", "Answer Relevancy", "Contextual Recall", "Contextual Precision"):
        return None
    verdicts = getattr(metric, "verdicts", None)
    if verdicts is None:
        return None
    if name == "Contextual Precision" and (
        any(v is None for v in verdicts)
        or (case is not None and len(case.retrieval_context or []) != len(verdicts))
    ):
        return None
    indexed = [(i, v.model_dump(mode="json") if hasattr(v, "model_dump") else v)
               for i, v in enumerate(verdicts) if v is not None]
    if any(not isinstance(v, dict) for _, v in indexed):
        return None
    verdicts = [v for _, v in indexed]
    values = [str(v.get("verdict", "")).lower() for v in verdicts]
    if any(v not in ("yes", "no", "borderline") for v in values):
        return None
    accepted = {"yes"}
    if name == "Answer Relevancy" or (name == "Faithfulness" and not getattr(metric, "penalize_ambiguous_claims", False)):
        accepted.add("borderline")
    texts = getattr(metric, "claims" if name == "Faithfulness" else "statements", []) or []
    if name == "Contextual Precision":
        texts = getattr(case, "retrieval_context", []) or []
    label = "Reference statement" if name == "Contextual Recall" else "Rank" if name == "Contextual Precision" else "Item"
    items = [
        {"label": texts[indexed[i][0]] if indexed[i][0] < len(texts) else f"{label} {indexed[i][0] + 1}",
         "verdict": value, "counted": value in accepted,
         "detail": verdicts[i].get("reason") or ""}
        for i, value in enumerate(values)
    ]
    numerator = sum(value in accepted for value in values)
    denominator = len(values)
    formula = {
        "Faithfulness": "F = accepted claim verdicts / all claim verdicts",
        "Answer Relevancy": "AR = accepted statement verdicts / all statement verdicts",
        "Contextual Recall": "CR = attributable reference statements / all reference statements",
        "Contextual Precision": "CP = Σ [P@j × rⱼ] / Σ rⱼ",
    }[name]
    if name == "Contextual Precision":
        relevant = 0
        numerator = 0
        for rank, (value, item) in enumerate(zip(values, items), 1):
            relevant += value == "yes"
            precision = relevant / rank
            contribution = precision if value == "yes" else 0
            item.update(rank=rank, relevant_so_far=relevant,
                        precision_at_rank=precision, contribution=contribution)
            numerator += contribution
        denominator = values.count("yes")
    expected = numerator / denominator if denominator else (1 if name in ("Faithfulness", "Answer Relevancy") else 0)
    if getattr(metric, "strict_mode", False) and expected < metric.threshold:
        expected = 0
    # A library mode change must not produce a plausible but incorrect derivation.
    if not math.isclose(expected, metric.score, abs_tol=1e-8):
        return None
    return {"formula": formula, "numerator": numerator, "denominator": denominator,
            "items": items, "empty_score": expected if not denominator else None,
            "strict_mode": getattr(metric, "strict_mode", False),
            "accepted_verdicts": sorted(accepted)}
