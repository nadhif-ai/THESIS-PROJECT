"""Explicit judge configuration; no Confident AI reporting or DeepEval tracing."""

from deepeval.models import OpenRouterModel
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    GEval,
    TurnFaithfulnessMetric,
    TurnRelevancyMetric,
    ConversationCompletenessMetric,
    ConversationalGEval,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
)
from deepeval.test_case import SingleTurnParams, MultiTurnParams
from app.admin import store
from app.config.settings import get_settings
from deepeval.models.llms.utils import trim_and_load_json
from openai import BadRequestError
from langsmith.wrappers import wrap_openai
from contextvars import ContextVar
import time
from testing.evals.calculations import RECIPE, ANNOTATED_RECIPE

THRESHOLD = 0.7
STEP_DEADLINE = ContextVar("evaluation_step_deadline", default=None)


class OpenRouterJudge(OpenRouterModel):
    def generate(self, prompt, schema=None):
        # DeepEval 4.2.8's sync path leaves async transports on a closed event loop.
        # A scoped synchronous client preserves the native model contract.
        with self.load_model(async_mode=False) as client:
            deadline = STEP_DEADLINE.get()
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining < 2:
                    raise TimeoutError("Evaluation step exceeded its time budget.")
                client = client.with_options(timeout=min(60, remaining), max_retries=0)
            client = wrap_openai(client, chat_name="quality-judge")
            parameters = dict(
                model=self.name,
                messages=self._build_messages(prompt),
                temperature=self.temperature,
                **self.generation_kwargs,
            )
            if schema:
                parameters["response_format"] = self._schema_response_format(schema)
            try:
                response = client.chat.completions.create(**parameters)
            except BadRequestError:
                if "response_format" not in parameters:
                    raise
                parameters.pop("response_format")
                response = client.chat.completions.create(**parameters)
            text = response.choices[0].message.content
            if not text:
                raise ValueError(
                    "Judge returned no visible output; check its token and reasoning settings."
                )
            cost = self.calculate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response=response,
            )
            return (
                schema.model_validate(trim_and_load_json(text)) if schema else text
            ), cost


def judge(model_name=None):
    s = get_settings()
    return OpenRouterJudge(
        model=model_name or store.get_setting("eval_model", s.eval_model),
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        temperature=0,
        timeout=90,
        max_retries=1,
        generation_kwargs={
            "max_tokens": 4096,
            "extra_body": {"reasoning": {"effort": "none"}},
        },
    )


def single_turn_metrics(review_notes=None, judge_model=None, recipe=RECIPE):
    model = judge(judge_model)
    mode = {"eval_mode": "llm"} if recipe in (RECIPE, ANNOTATED_RECIPE) else {}
    metrics = [
        FaithfulnessMetric(model=model, threshold=THRESHOLD, async_mode=False, **mode),
        AnswerRelevancyMetric(model=model, threshold=THRESHOLD, async_mode=False, **mode),
    ]
    if recipe == ANNOTATED_RECIPE:
        return metrics
    if recipe == RECIPE:
        return metrics + [
            ContextualRecallMetric(model=model, threshold=THRESHOLD, async_mode=False, **mode),
            ContextualPrecisionMetric(model=model, threshold=THRESHOLD, async_mode=False, **mode),
        ]
    # Resuming an older checkpoint must retain its original metric order.
    return metrics + [
        ContextualPrecisionMetric(model=model, threshold=THRESHOLD, async_mode=False),
        ContextualRecallMetric(model=model, threshold=THRESHOLD, async_mode=False),
        GEval(
            name="Business correctness",
            criteria="Compare the answer with the reference answer and business knowledge. Prices, units, quantities, conditions, and calculations must be correct. Appropriate clarification is better than inventing missing specifications."
            + (" Reviewed case guidance: " + review_notes if review_notes else ""),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
                SingleTurnParams.RETRIEVAL_CONTEXT,
            ],
            model=model,
            threshold=THRESHOLD,
            async_mode=False,
        ),
    ]


def conversational_metrics(judge_model=None, recipe="conversation-v2"):
    model = judge(judge_model)
    metrics = [
        TurnFaithfulnessMetric(model=model, threshold=THRESHOLD, async_mode=False),
        TurnRelevancyMetric(model=model, threshold=THRESHOLD, async_mode=False),
        ConversationCompletenessMetric(
            model=model, threshold=THRESHOLD, async_mode=False
        ),
    ]
    if recipe == "conversation-v2":
        return metrics
    return metrics + [
        ConversationalGEval(
            name="Business correctness",
            criteria="The conversation must communicate correct printing specifications, prices, units, calculations and policies grounded in the supplied knowledge. It should retain customer specifications across turns and clarify missing details. Judge against the expected outcome and context.",
            evaluation_params=[
                MultiTurnParams.EXPECTED_OUTCOME,
                MultiTurnParams.CONTEXT,
                MultiTurnParams.RETRIEVAL_CONTEXT,
            ],
            model=model,
            threshold=THRESHOLD,
            async_mode=False,
        ),
    ]
