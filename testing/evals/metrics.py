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
from openai import APIStatusError
from langsmith.wrappers import wrap_openai
from contextvars import ContextVar
import time
from testing.evals.calculations import RECIPE, ANNOTATED_RECIPE

THRESHOLD = 0.7
STEP_DEADLINE = ContextVar("evaluation_step_deadline", default=None)


class JudgeConfigurationError(ValueError):
    """Safe operator guidance without provider bodies, prompts or credentials."""


class JudgeOutputError(ValueError):
    """A judge response was incomplete rather than a valid low quality score."""


def judge_settings(model):
    # Calibrated DeepSeek reasoning needs headroom for both reasoning and visible JSON.
    effort = {
        "deepseek/deepseek-v4.1-flash": "low",
        "z-ai/glm-5.3-flash": "low",
        "anthropic/claude-haiku-5.5": "low",
    }.get(model, "provider_default")
    budget = 16384 if model == "deepseek/deepseek-v4.1-flash" else 4096
    return {"temperature": 0, "max_tokens": budget, "truncation_retry_max_tokens": budget * 2,
            "output_style": "compact-evidence-v1", "reasoning_effort": effort, "threshold": THRESHOLD}


def configuration_error(error):
    status = error.status_code
    if status not in (400, 401, 402, 403, 404, 422):
        return None
    guidance = {
        400: "The judge rejected its request parameters. Check model reasoning and structured-output support.",
        401: "The judge rejected authentication. Check the backend provider key.",
        402: "The judge has insufficient provider credits. Top up or choose an available scoring model.",
        403: "The judge is not permitted for this provider account. Check model access.",
        404: "The configured scoring model or endpoint was not found. Check Providers settings.",
        422: "The judge rejected the scoring schema or parameters. Choose a compatible scoring model.",
    }[status]
    return JudgeConfigurationError(f"Judge request rejected (HTTP {status}). {guidance} No quality score was produced.")


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
                messages=[{"role": "system", "content":
                    "Follow the metric rubric exactly and return only the requested JSON schema. "
                    "Keep each reason concise: at most two sentences and sixty words. "
                    "Do not repeat whole inputs or retrieved passages. Keep claims atomic and include every required verdict; do not omit evidence to shorten the response."},
                    *self._build_messages(prompt)],
                temperature=self.temperature,
                **self.generation_kwargs,
            )
            if schema:
                parameters["response_format"] = self._schema_response_format(schema)
            try:
                response = client.chat.completions.create(**parameters)
                if getattr(response.choices[0], "finish_reason", None) == "length":
                    parameters["max_tokens"] = min(judge_settings(self.name)["truncation_retry_max_tokens"], parameters.get("max_tokens", 4096) * 2)
                    if deadline is not None:
                        remaining = deadline - time.monotonic()
                        if remaining < 2:
                            raise TimeoutError("Evaluation step exceeded its time budget.")
                        parameters["timeout"] = min(60, remaining)
                    response = client.chat.completions.create(**parameters)
            except APIStatusError as error:
                failure = configuration_error(error)
                if failure:
                    raise failure from None
                raise
            text = response.choices[0].message.content
            if getattr(response.choices[0], "finish_reason", None) == "length":
                usage = getattr(response, "usage", None)
                details = getattr(usage, "completion_tokens_details", None)
                raise JudgeOutputError(
                    f"The judge exhausted its output-token budget (limit {parameters.get('max_tokens')}, "
                    f"completion tokens {getattr(usage, 'completion_tokens', None)}, "
                    f"reasoning tokens {getattr(details, 'reasoning_tokens', None)}, visible characters {len(text or '')}). "
                    "No score was produced; reduce reasoning effort or increase the scoring budget."
                )
            if not text:
                raise JudgeOutputError(
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
    selected = model_name or store.get_setting("eval_model", s.eval_model)
    config = judge_settings(selected)
    return OpenRouterJudge(
        model=selected,
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        temperature=0,
        timeout=90,
        max_retries=1,
        generation_kwargs={
            "max_tokens": config["max_tokens"],
            **({"extra_body": {"reasoning": {"effort": config["reasoning_effort"]}}} if config["reasoning_effort"] != "provider_default" else {}),
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
