"""DeepEval pytest contract with LangSmith traces and feedback."""

import csv
import os
import uuid
from pathlib import Path
import pytest

PAID = os.getenv("RUN_PAID_EVALS") == "1"
KIND = os.getenv("EVAL_DATASET", "legacy")
LIMIT = int(os.getenv("EVAL_CASE_LIMIT", "10"))
ROOT = Path(__file__).resolve().parents[2]
ROWS = list(
    csv.DictReader((ROOT / "testing/test_dataset.csv").open(encoding="utf-8-sig"))
)[:LIMIT]
if PAID and KIND == "audited":
    from testing.evals.runner import load_cases

    ROWS = load_cases(KIND, LIMIT)


@pytest.fixture(scope="module")
def chain():
    from app.dependencies import initialize_rag_system, get_rag_chain

    initialize_rag_system()
    return get_rag_chain()


@pytest.fixture(scope="module")
def knowledge_snapshot(chain):
    from app.admin import store
    from app.backend.models import answer_defaults
    from app.config.settings import get_settings

    if os.getenv("EVAL_KNOWLEDGE_VERSION"):
        raise ValueError("EVAL_KNOWLEDGE_VERSION is retired. New evaluations use current synchronized knowledge.")
    selected = store.version()
    if not selected["records"]:
        raise ValueError("Sync searchable knowledge before evaluation.")
    settings = get_settings()
    config = store.get_settings_values({**answer_defaults(settings),
            "eval_model": settings.eval_model, "semantic_top_k": settings.semantic_top_k})
    from app.admin.prompt_settings import active_snapshot
    config["prompt_snapshot"] = active_snapshot()
    return selected, config


def check_and_report(case, metrics, run_id, client):
    from deepeval import assert_test

    try:
        assert_test(test_case=case, metrics=metrics, run_async=False)
    finally:
        client.flush(timeout=30)
        for metric in metrics:
            if metric.score is not None:
                client.create_feedback(
                    run_id=run_id,
                    key=metric.__name__,
                    score=metric.score,
                    comment=metric.reason,
                )


@pytest.mark.skipif(
    not PAID or KIND not in ("legacy", "audited"),
    reason="Set RUN_PAID_EVALS=1 and select legacy or reviewed audited QA references.",
)
@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS])
def test_single_question(row, chain, knowledge_snapshot):
    from app.backend.models import answer_selection
    from deepeval.test_case import LLMTestCase
    from langsmith import Client, trace, tracing_context
    from testing.evals.metrics import single_turn_metrics

    client = Client()
    selected, config = knowledge_snapshot
    model_provider, model = answer_selection(config)
    metrics = single_turn_metrics(row.get("review_notes"), config["eval_model"])
    with tracing_context(client=client):
        with trace(
            "deepeval-quality-test",
            inputs={"question": row["question"]},
            metadata={"channel": "evaluation", "case_id": row["id"], "prompt_sha256": config["prompt_snapshot"]["sha256"]},
        ) as parent:
            response = chain.run(
                question=row["question"],
                session_id="eval-pytest-" + uuid.uuid4().hex,
                channel="evaluation",
                history_turns=[],
                namespace=selected["namespace"],
                model=model, model_provider=model_provider, top_k=config["semantic_top_k"],
                prompt_config=config["prompt_snapshot"],
            )
            assert not response.error, response.error
            case = LLMTestCase(
                input=row["question"],
                actual_output=response.answer,
                expected_output=row["ground_truth"],
                retrieval_context=[c["text"] for c in response.retrieval_context],
                metadata={"prompt_sha256": config["prompt_snapshot"]["sha256"],
                          "prompt_snapshot": config["prompt_snapshot"]},
            )
            parent.end(outputs={"answer": response.answer})
        check_and_report(case, metrics, str(parent.id), client)


@pytest.mark.skipif(
    not PAID or KIND != "conversations",
    reason="Select EVAL_DATASET=conversations after human dataset review.",
)
def test_conversation(chain, knowledge_snapshot):
    from app.backend.models import answer_selection
    from deepeval.dataset import ConversationalGolden
    from deepeval.simulator import ConversationSimulator
    from deepeval.test_case import Turn
    from langsmith import Client, trace, tracing_context
    from testing.evals.runner import load_cases
    from testing.evals.metrics import judge, conversational_metrics

    rows = load_cases("conversations", LIMIT)
    selected, config = knowledge_snapshot
    model_provider, model = answer_selection(config)
    client = Client()
    for row in rows:

        def callback(input, turns, thread_id):
            response = chain.run(
                question=input,
                session_id="eval-pytest-" + str(thread_id),
                channel="evaluation",
                namespace=selected["namespace"], model=model, model_provider=model_provider, top_k=config["semantic_top_k"],
                prompt_config=config["prompt_snapshot"],
                history_turns=[
                    (turns[i].content, turns[i + 1].content)
                    for i in range(0, len(turns) - 1, 2)
                    if turns[i].role == "user" and turns[i + 1].role == "assistant"
                ],
            )
            assert not response.error, response.error
            return Turn(
                role="assistant",
                content=response.answer,
                retrieval_context=[c["text"] for c in response.retrieval_context],
            )

        golden = ConversationalGolden(
            **{
                key: value
                for key, value in row.items()
                if key in ConversationalGolden.model_fields and key != "id"
            }
        )
        with tracing_context(client=client):
            with trace(
                "deepeval-conversation-test",
                inputs={"scenario": row["scenario"]},
                metadata={"channel": "evaluation", "prompt_sha256": config["prompt_snapshot"]["sha256"]},
            ) as parent:
                case = ConversationSimulator(
                    model_callback=callback,
                    simulator_model=judge(config["eval_model"]),
                    max_concurrent=1,
                    async_mode=False,
                    language="Indonesian",
                ).simulate(conversational_goldens=[golden], max_user_simulations=4)[0]
                case.metadata = {"prompt_sha256": config["prompt_snapshot"]["sha256"],
                                 "prompt_snapshot": config["prompt_snapshot"]}
                parent.end(
                    outputs={"turns": [t.model_dump(mode="json") for t in case.turns]}
                )
            check_and_report(case, conversational_metrics(config["eval_model"]), str(parent.id), client)
