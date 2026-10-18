"""Checkpoint between answers, conversational turns and individual DeepEval metrics."""

import hashlib
import json
import os
import time
import uuid
from importlib.metadata import version as package_version

from langsmith import Client, trace, tracing_context
from langsmith.utils import LangSmithNotFoundError
from deepeval.test_case import LLMTestCase, ConversationalTestCase, Turn
from deepeval.dataset import ConversationalGolden
from deepeval.simulator import ConversationSimulator

from app.admin import durable_jobs, kb_store, store
from app.config.settings import get_settings
from testing.evals.metrics import (
    STEP_DEADLINE,
    single_turn_metrics,
    conversational_metrics,
    judge,
)
from testing.evals.runner import load_cases, SINGLE_TURN, _metric_results, retry_report


def submit(dataset, limit):
    rows = load_cases(dataset, limit)
    if not rows:
        raise ValueError("The selected reference dataset has no eligible cases.")
    settings = get_settings()
    configuration = store.get_settings_values(
        {
            "openrouter_model": settings.openrouter_model,
            "eval_model": settings.eval_model,
            "semantic_top_k": settings.semantic_top_k,
        }
    )
    from app.dependencies import get_rag_chain

    identifier = kb_store.create_evaluation(
        {"dataset": dataset, "limit": limit},
        {
            "rows": rows,
            "configuration": configuration,
            "prompt_sha256": get_rag_chain().prompt_fingerprint,
        },
    )
    try:
        durable_jobs.dispatch(identifier)
    except RuntimeError:
        return {"job_id": identifier, "dispatch_pending": True}
    return {"job_id": identifier}


def _prepare(identifier, state):
    from app.dependencies import get_rag_chain

    snapshot, config = state.pop("snapshot"), state["configuration"]
    manifest = snapshot["manifest"]
    result = {
        "id": identifier,
        "dataset": json.loads(kb_store.work(identifier)["payload"])["dataset"],
        "knowledge_version": snapshot["id"],
        "namespace": snapshot["namespace"],
        "started_at": store.now(),
        "model": config["openrouter_model"],
        "judge": config["eval_model"],
        "runtime_top_k": config["semantic_top_k"],
        "chunking": manifest.get("chunking"),
        "corpus_sha256": manifest.get("corpus_sha256"),
        "embedding_model": manifest["embedding"]["model"],
        "embedding": manifest["embedding"],
        "vector_index": manifest["vector_index"],
        "evaluation_recipe": "retrieval-precision-recall-v1",
        "deepeval_version": package_version("deepeval"),
        "prompt_sha256": state.get("prompt_sha256", get_rag_chain().prompt_fingerprint),
        "dataset_sha256": hashlib.sha256(
            json.dumps(state["rows"], sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "judge_settings": {
            "temperature": 0,
            "max_tokens": 4096,
            "reasoning_effort": "none",
            "threshold": 0.7,
        },
        "cases": [],
        "experiment_name": f"avg-{identifier[:12]}",
        "reporting_error": None,
    }
    client = Client(timeout_ms=10000)
    try:
        name = f"avg-{result['dataset']}-{result['dataset_sha256'][:12]}"
        try:
            dataset = client.read_dataset(dataset_name=name)
        except LangSmithNotFoundError:
            dataset = client.create_dataset(
                dataset_name=name, description="Reviewed chatbot evaluation references"
            )
        try:
            project = client.read_project(project_name=result["experiment_name"])
        except LangSmithNotFoundError:
            project = client.create_project(
                result["experiment_name"],
                reference_dataset_id=dataset.id,
                metadata={
                    k: result[k]
                    for k in (
                        "knowledge_version",
                        "model",
                        "judge",
                        "runtime_top_k",
                        "chunking",
                        "embedding",
                        "vector_index",
                        "evaluation_recipe",
                    )
                },
            )
        result.update(project_id=str(project.id), dataset_id=str(dataset.id))
    except Exception as error:
        result["reporting_error"] = type(error).__name__
    state.update(phase="answering", result=result)


def _example(client, result, row):
    if not result.get("dataset_id"):
        return None
    identifier = str(uuid.uuid5(uuid.UUID(result["dataset_id"]), str(row["id"])))
    try:
        try:
            client.read_example(identifier)
        except LangSmithNotFoundError:
            client.create_example(
                dataset_id=result["dataset_id"],
                example_id=identifier,
                inputs={
                    "question": row.get("question"),
                    "scenario": row.get("scenario"),
                },
                outputs={
                    "answer": row.get("ground_truth"),
                    "expected_outcome": row.get("expected_outcome"),
                },
            )
        return identifier
    except Exception as error:
        result["reporting_error"] = type(error).__name__
        return None


def _answer(identifier, state, row):
    from app.dependencies import get_rag_chain

    result = state["result"]
    chain = get_rag_chain()
    if chain.prompt_fingerprint != result["prompt_sha256"]:
        raise ValueError(
            "Prompt changed after submission; start a new evaluation to keep its cases consistent."
        )
    record = state.get("record") or {"id": row["id"], "metrics": []}
    client = Client(timeout_ms=10000)
    example = _example(client, result, row)
    with tracing_context(
        client=client,
        project_name=result["experiment_name"]
        if result.get("project_id")
        else os.getenv("LANGSMITH_PROJECT"),
    ):
        with trace(
            "evaluation-case",
            inputs={
                "case_id": row["id"],
                "question": row.get("question"),
                "scenario": row.get("scenario"),
            },
            reference_example_id=example,
            metadata={
                "channel": "evaluation",
                "knowledge_version": result["knowledge_version"],
            },
        ) as tree:
            record.update(trace_id=str(tree.id))
            if result["dataset"] in SINGLE_TURN:
                answer = chain.run(
                    question=row["question"],
                    session_id=f"eval_{identifier}_{row['id']}",
                    namespace=result["namespace"],
                    channel="evaluation",
                    top_k=result["runtime_top_k"],
                    model=result["model"],
                )
                record.update(
                    input=row["question"],
                    answer=answer.answer,
                    expected_output=row["ground_truth"],
                    retrieval_context=answer.retrieval_context,
                    usage=answer.usage,
                    latency_seconds=answer.latency_seconds,
                    reference_guidance=row.get("review_notes"),
                )
                if answer.error:
                    record["error"] = answer.error
                state["phase"] = "scoring"
            else:
                saved = record.get("turns", [])
                golden = ConversationalGolden(
                    **{
                        key: value
                        for key, value in row.items()
                        if key in ConversationalGolden.model_fields
                        and key not in ("id", "turns")
                    },
                    turns=[Turn(**t) for t in saved] or None,
                )

                def callback(input, turns, thread_id):
                    response = chain.run(
                        question=input,
                        session_id=f"eval_{identifier}_{row['id']}",
                        namespace=result["namespace"],
                        channel="evaluation",
                        top_k=result["runtime_top_k"],
                        model=result["model"],
                    )
                    if response.error:
                        raise RuntimeError(response.error)
                    return Turn(
                        role="assistant",
                        content=response.answer,
                        retrieval_context=[
                            c["text"] for c in response.retrieval_context
                        ],
                    )

                simulator = ConversationSimulator(
                    model_callback=callback,
                    simulator_model=judge(result["judge"]),
                    max_concurrent=1,
                    async_mode=False,
                    language="Indonesian",
                )
                case = simulator.simulate(
                    conversational_goldens=[golden], max_user_simulations=1
                )[0]
                record["turns"] = [turn.model_dump(mode="json") for turn in case.turns]
                record["simulation_recipe"] = "seeded-pairs-max-four-v1"
                if (
                    len(case.turns) == len(saved)
                    or sum(t.role == "assistant" for t in case.turns) >= 4
                ):
                    state["phase"] = "scoring"
                record.update(
                    scenario=row["scenario"],
                    expected_outcome=row.get("expected_outcome"),
                    context=row.get("context"),
                )
            tree.end(outputs=record)
            try:
                record["trace_url"] = tree.get_url()
            except Exception:
                record["trace_url"] = None
    try:
        client.flush(timeout=5)
    except Exception as error:
        result["reporting_error"] = type(error).__name__
    state["record"] = record


def evaluation_step(identifier, state, token):
    deadline = STEP_DEADLINE.set(time.monotonic() + 180)
    try:
        result, done = _step(identifier, state)
    finally:
        STEP_DEADLINE.reset(deadline)
    completed = len(result.get("cases", [])) if result else 0
    record = state.get("record", {})
    row = state["rows"][completed] if completed < len(state["rows"]) else {}
    progress = {
        "phase": state["phase"],
        "completed": completed,
        "total": len(state["rows"]),
        "case_id": row.get("id"),
        "case_label": row.get("question") or row.get("scenario"),
        "metrics_completed": len(record.get("metrics", [])),
        "metrics_total": 5 if result and result["dataset"] in SINGLE_TURN else 4,
        "errors": sum(
            bool(c.get("error")) or any(m.get("error") for m in c["metrics"])
            for c in result.get("cases", [])
        )
        if result
        else 0,
    }
    return state, progress, result, done


def _step(identifier, state):
    phase = state["phase"]
    if phase == "prepare":
        _prepare(identifier, state)
        return state["result"], False
    result = state["result"]
    if phase == "reporting":
        result = retry_report(identifier)
        state.update(result=result, phase="completed")
        return result, True
    row = state["rows"][len(result["cases"])]
    if phase == "answering":
        _answer(identifier, state, row)
        return result, False
    record = state["record"]
    if not record.get("error"):
        if result["dataset"] in SINGLE_TURN:
            case = LLMTestCase(
                input=record["input"],
                actual_output=record["answer"],
                expected_output=record["expected_output"],
                retrieval_context=[c["text"] for c in record["retrieval_context"]],
            )
            metrics = single_turn_metrics(row.get("review_notes"), result["judge"])
        else:
            case = ConversationalTestCase(
                turns=[Turn(**t) for t in record["turns"]],
                scenario=row["scenario"],
                expected_outcome=row.get("expected_outcome"),
                context=row.get("context"),
            )
            metrics = conversational_metrics(result["judge"])
        index = len(record["metrics"])
        with tracing_context(
            project_name=result["experiment_name"]
            if result.get("project_id")
            else os.getenv("LANGSMITH_PROJECT")
        ):
            with trace(
                "evaluation-metric",
                inputs={"case_id": row["id"], "metric": metrics[index].__name__},
                metadata={
                    "knowledge_version": result["knowledge_version"],
                    "evaluation_id": identifier,
                },
            ):
                record["metrics"].extend(_metric_results(case, [metrics[index]]))
        if len(record["metrics"]) < len(metrics):
            return result, False
    result["cases"].append(state.pop("record"))
    if len(result["cases"]) < len(state["rows"]):
        state["phase"] = "answering"
    else:
        result["completed_at"] = store.now()
        names = {m["name"] for c in result["cases"] for m in c["metrics"]}
        result["averages"] = {
            name: sum(values) / len(values) if values else None
            for name in names
            for values in [
                [
                    m["score"]
                    for c in result["cases"]
                    for m in c["metrics"]
                    if m["name"] == name and m["score"] is not None
                ]
            ]
        }
        state["phase"] = "reporting"
    return result, False
