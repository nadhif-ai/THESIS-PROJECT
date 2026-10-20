import csv
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from importlib.metadata import version as package_version

from langsmith import Client, trace, tracing_context
from langsmith.utils import LangSmithNotFoundError
from deepeval.test_case import LLMTestCase, Turn
from deepeval.dataset import ConversationalGolden
from deepeval.simulator import ConversationSimulator

from app.admin import store
from app.config.settings import get_settings
from testing.evals.metrics import single_turn_metrics, conversational_metrics, judge
from testing.evals.calculations import (
    RECIPE, judge_calculation, retrieval_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = Path(__file__).with_name(".dataset.json")
REVIEW = Path(__file__).with_name("dataset-review.json")
STALE = Path(__file__).with_name("dataset-stale.json")
QA_DATASET = Path(__file__).with_name("qa-reference-candidates.json")
QA_REVIEW = Path(__file__).with_name("qa-reference-review.json")
SINGLE_TURN = ("legacy", "audited")


def candidate_rows():
    data = json.loads(DATASET.read_text())
    return (
        data
        if isinstance(data, list)
        else data.get("conversational_goldens", data.get("goldens", []))
    )


def qa_rows():
    return json.loads(QA_DATASET.read_text())


def dataset_status(kind="conversations"):
    if kind == "audited":
        if not QA_DATASET.exists():
            return {"exists": False, "reviewed": False, "count": 0, "held_count": 0}
        digest = hashlib.sha256(QA_DATASET.read_bytes()).hexdigest()
        rows = qa_rows()
        return {
            "exists": True,
            "reviewed": (QA_REVIEW.exists() and json.loads(QA_REVIEW.read_text()).get("sha256") == digest)
            or store.get_setting("dataset_review:audited", {}).get("sha256") == digest,
            "sha256": digest,
            "count": sum(row.get("review_status") != "hold" for row in rows),
            "held_count": sum(row.get("review_status") == "hold" for row in rows),
            "path": str(QA_DATASET),
            "cases": rows,
        }
    if not DATASET.exists():
        return {"exists": False, "reviewed": False, "count": 0}
    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    stale = STALE.exists() and json.loads(STALE.read_text()).get("sha256") == digest
    reviewed = (
        ((REVIEW.exists() and json.loads(REVIEW.read_text()).get("sha256") == digest)
         or store.get_setting("dataset_review:conversations", {}).get("sha256") == digest)
        and not stale
    )
    rows = candidate_rows()
    return {
        "exists": True,
        "reviewed": reviewed,
        "stale": stale,
        "count": len(rows),
        "sha256": digest,
        "path": str(DATASET),
        "cases": rows,
    }


def mark_reviewed(kind="conversations"):
    if kind == "audited":
        status = dataset_status(kind)
        if not status["exists"] or not status["count"]:
            raise ValueError("No QA references are available for review.")
        rows = qa_rows()
        identifiers = [row.get("id") for row in rows]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("QA case IDs must be unique.")
        for row in rows:
            if row.get("review_status") not in ("candidate", "hold") or not all(
                isinstance(row.get(key), str) and row[key].strip()
                for key in ("id", "question", "ground_truth", "review_notes")
            ):
                raise ValueError(
                    "Each QA case needs a question, reference, review notes and valid status."
                )
        store.set_settings({"dataset_review:audited": {"sha256": status["sha256"], "reviewed_at": store.now()}})
        return dataset_status(kind)
    status = dataset_status()
    if not status["exists"]:
        raise ValueError("Generate candidate scenarios first.")
    if status.get("stale"):
        raise ValueError(
            "Conversation references contain superseded knowledge. Correct or regenerate their contexts and outcomes before review."
        )
    for row in candidate_rows():
        golden = ConversationalGolden(
            **{
                key: value
                for key, value in row.items()
                if key in ConversationalGolden.model_fields
            }
        )
        if not golden.scenario or not golden.expected_outcome:
            raise ValueError("Every scenario needs a reviewed expected outcome.")
    store.set_settings({"dataset_review:conversations": {"sha256": status["sha256"], "reviewed_at": store.now()}})
    return dataset_status()


def generate_candidates(version_id):
    if DATASET.exists():
        raise ValueError(
            "A candidate dataset already exists. Review it before generating a replacement."
        )
    item = store.version(version_id)
    from app.backend.vectorstore import require_compatible_version
    require_compatible_version(item)
    records = item["records"]
    if not records:
        raise ValueError("Index knowledge before generating scenarios.")
    # Reuse the indexed business contexts; this avoids needing another embedding API.
    groups = [records[i::20] for i in range(min(20, len(records)))]
    folder = store.data_path() / "evaluations"
    folder.mkdir(exist_ok=True)
    contexts = folder / "generation-contexts.json"
    contexts.write_text(
        json.dumps(
            [[r["document"] for r in group] for group in groups], ensure_ascii=False
        )
    )
    s = get_settings()
    env = dict(
        os.environ,
        USE_OPENROUTER_MODEL="1",
        OPENROUTER_MODEL_NAME=store.get_setting("eval_model", s.eval_model),
    )
    command = [
        str(Path(sys.executable).parent / "deepeval"),
        "generate",
        "--method",
        "contexts",
        "--variation",
        "multi-turn",
        "--contexts-file",
        str(contexts),
        "--max-goldens-per-context",
        "2",
        "--sync-mode",
        "--max-concurrent",
        "1",
        "--model",
        env["OPENROUTER_MODEL_NAME"],
        "--output-dir",
        str(DATASET.parent),
        "--file-name",
        "candidate-conversations",
        "--scenario-context",
        "Indonesian customers asking Asia Visual Grafika about printing materials, files, prices and shop policies through WhatsApp.",
        "--conversational-task",
        "Answer using the supplied knowledge, remember specifications, clarify missing information, and avoid unsupported prices.",
        "--participant-roles",
        "Customer and printing business support assistant",
        "--scenario-format",
        "Natural Indonesian WhatsApp conversation scenario with colloquial abbreviations and follow-up questions.",
        "--expected-outcome-format",
        "Indonesian description of the correct business facts and customer outcome.",
    ]
    with (folder / "generation.log").open("w") as log:
        result = subprocess.run(
            command, cwd=ROOT, env=env, stdout=log, stderr=log, timeout=1800
        )
    generated = DATASET.parent / "candidate-conversations.json"
    if result.returncode or not generated.exists():
        raise ValueError(
            "Dataset generation failed. Inspect data/evaluations/generation.log and provider settings."
        )
    generated.rename(DATASET)
    rows = candidate_rows()
    if len(rows) > 40:
        DATASET.write_text(json.dumps(rows[:40], ensure_ascii=False, indent=2) + "\n")
    return {
        "count": len(candidate_rows()),
        "reviewed": False,
        "path": str(DATASET),
        "version_id": version_id,
    }


def load_cases(dataset, limit):
    if dataset == "legacy":
        with (ROOT / "testing/test_dataset.csv").open(encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))[:limit]
    if dataset == "audited":
        if not dataset_status(dataset)["reviewed"]:
            raise ValueError(
                "Review the QA references first. Held cases remain excluded."
            )
        return [row for row in qa_rows() if row["review_status"] != "hold"][:limit]
    status = dataset_status()
    if not status["reviewed"]:
        raise ValueError(
            "Review generated scenarios and mark the dataset reviewed first."
        )
    # Keep every fifth scenario held out. Development runs cannot select these.
    return [
        dict(row, id=f"conversation-{i + 1}")
        for i, row in enumerate(candidate_rows())
        if (i % 5 == 0 if dataset == "heldout" else i % 5 != 0)
    ][:limit]


def _metric_results(case, metrics, progress=None):
    scores = []
    for metric in metrics:
        if progress:
            progress(phase="scoring", metric=metric.__name__, metrics_completed=len(scores), metrics_total=len(metrics))
        try:
            metric.measure(case)
            scores.append(
                {
                    "name": metric.__name__,
                    "score": metric.score,
                    "reason": metric.reason,
                    "threshold": metric.threshold,
                    "passed": metric.is_successful(),
                    "method": "llm_judge",
                    "calculation": judge_calculation(metric, case),
                }
            )
        except Exception as error:
            scores.append(
                {
                    "name": metric.__name__,
                    "score": None,
                    "reason": None,
                    "threshold": metric.threshold,
                    "passed": None,
                    "error": type(error).__name__,
                }
            )
        if progress:
            progress(metrics_completed=len(scores))
    return scores


def _sync_dataset(client, name, rows, kind):
    fingerprint = hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:12]
    dataset_name = f"avg-{name}-{fingerprint}"
    try:
        dataset = client.read_dataset(dataset_name=dataset_name)
    except LangSmithNotFoundError:
        dataset = client.create_dataset(
            dataset_name=dataset_name, description="Versioned chatbot evaluation cases"
        )
    examples = {}
    for row in rows:
        identifier = str(uuid.uuid5(uuid.UUID(str(dataset.id)), str(row["id"])))
        try:
            example = client.read_example(identifier)
        except LangSmithNotFoundError:
            inputs = (
                {"question": row["question"]}
                if kind in SINGLE_TURN
                else {"scenario": row["scenario"]}
            )
            outputs = (
                {"answer": row["ground_truth"]}
                if kind in SINGLE_TURN
                else {"expected_outcome": row.get("expected_outcome")}
            )
            example = client.create_example(
                inputs=inputs,
                outputs=outputs,
                dataset_id=dataset.id,
                example_id=identifier,
            )
        examples[row["id"]] = str(example.id)
    return dataset, examples


def run_evaluation(job_id, version_id=None, dataset="legacy", limit=10, configuration=None):
    from app.dependencies import get_rag_chain
    from app.admin.jobs import update_progress
    from app.admin.prompt_settings import active_snapshot

    captured_prompt = active_snapshot()

    def progress(**fields):
        update_progress(job_id, **fields)

    item = store.version(version_id)
    from app.backend.vectorstore import require_compatible_version
    require_compatible_version(item)
    rows = load_cases(dataset, limit)
    progress(phase="preparing", completed=0, total=len(rows), errors=0)
    s = get_settings()
    configuration = configuration or store.get_settings_values({
        "openrouter_model": s.openrouter_model,
        "eval_model": s.eval_model,
        "semantic_top_k": s.semantic_top_k,
    })
    folder = store.data_path() / "evaluations" / job_id
    folder.mkdir(parents=True, exist_ok=True)
    result = {
        "id": job_id,
        "dataset": dataset,
        "knowledge_version": item["id"],
        "namespace": item["namespace"],
        "started_at": store.now(),
        "model": configuration["openrouter_model"],
        "judge": configuration["eval_model"],
        "runtime_top_k": configuration["semantic_top_k"],
        "chunking": item["manifest"].get(
            "chunking",
            {"chunk_size": 1500, "chunk_overlap": 200, "preprocessing": "legacy"},
        ),
        "corpus_sha256": item["manifest"].get("corpus_sha256"),
        "evaluation_recipe": RECIPE if dataset in SINGLE_TURN else "conversation-v2",
        "retrieval_manifest": retrieval_manifest(item["records"]),
        "embedding_model": item["manifest"]["embedding"]["model"],
        "embedding": item["manifest"]["embedding"],
        "vector_index": item["manifest"]["vector_index"],
        "deepeval_version": package_version("deepeval"),
        "cases": [],
        "experiment_name": f"avg-{dataset}-{job_id[:12]}",
        "reporting_error": None,
        "prompt_snapshot": captured_prompt,
        "prompt_sha256": captured_prompt["sha256"],
    }
    client = Client()
    examples = {}
    project = None
    try:
        ds, examples = _sync_dataset(client, dataset, rows, dataset)
        project = client.create_project(
            result["experiment_name"],
            reference_dataset_id=ds.id,
            metadata={
                "knowledge_version": item["id"],
                "model": result["model"],
                "judge": result["judge"],
                "dataset": dataset,
                "top_k": result["runtime_top_k"],
                "chunking": result["chunking"],
                "evaluation_recipe": result["evaluation_recipe"],
                "embedding": result["embedding"],
                "vector_index": result["vector_index"],
            },
        )
        result["project_id"] = str(project.id)
    except Exception as error:
        result["reporting_error"] = type(error).__name__
    chain = get_rag_chain()
    result["dataset_sha256"] = hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    result["judge_settings"] = {
        "temperature": 0,
        "max_tokens": 4096,
        "reasoning_effort": "none",
        "threshold": 0.7,
    }
    for row in rows:
        progress(phase="answering", case_id=row["id"], case_label=row.get("question") or row.get("scenario"), metric=None, metrics_completed=0, metrics_total=0)
        with tracing_context(
            client=client,
            project_name=result["experiment_name"]
            if project
            else os.getenv("LANGSMITH_PROJECT"),
        ):
            with trace(
                "evaluation-case",
                inputs={
                    "case_id": row["id"],
                    "question": row.get("question"),
                    "scenario": row.get("scenario"),
                },
                reference_example_id=examples.get(row["id"]),
                metadata={"channel": "evaluation", "knowledge_version": item["id"]},
            ) as tree:
                record = {"id": row["id"], "trace_id": str(tree.id), "metrics": []}
                if dataset in SINGLE_TURN:
                    answer = chain.run(
                        question=row["question"],
                        session_id=f"eval_{job_id}_{row['id']}",
                        namespace=item["namespace"],
                        channel="evaluation",
                        top_k=result["runtime_top_k"],
                        model=result["model"],
                        prompt_config=captured_prompt,
                    )
                    record.update(
                        input=row["question"],
                        answer=answer.answer,
                        expected_output=row["ground_truth"],
                        retrieval_context=answer.retrieval_context,
                        usage=answer.usage,
                        latency_seconds=answer.latency_seconds,
                        reference_guidance=row.get("review_notes"),
                        retrieval_annotations=row.get("retrieval_annotations"),
                    )
                    if answer.error:
                        record["error"] = answer.error
                    else:
                        case = LLMTestCase(
                            input=row["question"],
                            actual_output=answer.answer,
                            expected_output=row["ground_truth"],
                            retrieval_context=[
                                c["text"] for c in answer.retrieval_context
                            ],
                        )
                        record["metrics"] = _metric_results(
                            case,
                            single_turn_metrics(
                                row.get("review_notes"), result["judge"]
                            ),
                            progress,
                        )
                else:

                    def callback(input, turns, thread_id):
                        response = chain.run(
                            question=input,
                            session_id=f"eval_{job_id}_{thread_id}",
                            namespace=item["namespace"],
                            channel="evaluation",
                            top_k=result["runtime_top_k"],
                            model=result["model"],
                            prompt_config=captured_prompt,
                            history_turns=[
                                (turns[i].content, turns[i + 1].content)
                                for i in range(0, len(turns) - 1, 2)
                                if turns[i].role == "user" and turns[i + 1].role == "assistant"
                            ],
                        )
                        if response.error:
                            raise ValueError(response.error)
                        return Turn(
                            role="assistant",
                            content=response.answer,
                            retrieval_context=[
                                c["text"] for c in response.retrieval_context
                            ],
                        )

                    golden = ConversationalGolden(
                        **{
                            key: value
                            for key, value in row.items()
                            if key in ConversationalGolden.model_fields and key != "id"
                        }
                    )
                    simulator = ConversationSimulator(
                        model_callback=callback,
                        simulator_model=judge(result["judge"]),
                        max_concurrent=1,
                        async_mode=False,
                        language="Indonesian",
                    )
                    case = simulator.simulate(
                        conversational_goldens=[golden], max_user_simulations=4
                    )[0]
                    record.update(
                        scenario=row["scenario"],
                        expected_outcome=row.get("expected_outcome"),
                        turns=[turn.model_dump(mode="json") for turn in case.turns],
                    )
                    record["metrics"] = _metric_results(
                        case, conversational_metrics(result["judge"]), progress
                    )
                tree.end(outputs=record)
                try:
                    record["trace_url"] = tree.get_url()
                except Exception:
                    record["trace_url"] = None
                result["cases"].append(record)
                (folder / "results.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2) + "\n"
                )
                progress(completed=len(result["cases"]), errors=sum(bool(case.get("error")) or any(metric.get("error") for metric in case["metrics"]) for case in result["cases"]))
    progress(phase="reporting", case_id=None, case_label=None, metric=None)
    client.flush(timeout=30)
    result["completed_at"] = store.now()
    names = {score["name"] for row in result["cases"] for score in row["metrics"]}
    result["averages"] = {
        name: sum(values) / len(values) if values else None
        for name in names
        for values in [
            [
                score["score"]
                for row in result["cases"]
                for score in row["metrics"]
                if score["name"] == name and score["score"] is not None
            ]
        ]
    }
    (folder / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    return retry_report(job_id)


def report_metric(client, result, row, score):
    if score.get("status") == "unavailable":
        return
    identifier = str(uuid.uuid5(uuid.UUID(row["trace_id"]), score["name"]))
    try:
        client.read_feedback(identifier)
    except LangSmithNotFoundError:
        client.create_feedback(
            run_id=row["trace_id"], key=score["name"], score=score["score"],
            comment=score.get("reason") or score.get("error"), feedback_id=identifier,
            session_id=result["project_id"], error=score["score"] is None,
            source_info={"framework": score.get("method", "deepeval"), "threshold": score.get("threshold"),
                         "version": result["evaluation_recipe"] if score.get("method") else result["deepeval_version"]})


def retry_report(evaluation_id):
    if not evaluation_id.isalnum():
        raise ValueError("Invalid evaluation ID.")
    result = store.evaluation_result(evaluation_id)
    path = None
    if result is None:
        path = store.data_path() / "evaluations" / evaluation_id / "results.json"
        result = json.loads(path.read_text())
    client = Client()
    try:
        if not result.get("project_id"):
            raise ValueError(
                "No LangSmith experiment was created; local scores are available."
            )
        for row in result["cases"]:
            for score in row["metrics"]:
                report_metric(client, result, row, score)
        result["reporting_error"] = None
        project = client.read_project(project_id=result["project_id"])
        result["experiment_url"] = project.url
    except Exception as error:
        result["reporting_error"] = type(error).__name__
    store.save_evaluation_result(evaluation_id, result)
    if path is not None:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result
