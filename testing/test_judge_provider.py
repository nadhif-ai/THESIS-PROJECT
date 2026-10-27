"""Public judge adapter regressions; fake HTTP clients never call paid providers."""

from contextlib import nullcontext
from types import SimpleNamespace

import httpx
from openai import BadRequestError
from pydantic import BaseModel
import pytest
from deepeval.test_case import LLMTestCase

from testing.evals import metrics
from testing.evals.runner import _metric_results
from app.config.settings import get_settings


class Probe(BaseModel):
    ok: bool


@pytest.mark.parametrize("model", ["azure/gpt-5.6-terra-20260709-global", "azure/gpt-5.6-luna-20260709-global", "cx/gpt-6-luna[1m]", "glm/glm-5.3-flash"])
def test_9router_scoring_uses_its_own_endpoint_and_key(monkeypatch, model):
    import json
    from openai import OpenAI
    from deepeval.models.llms import gateway_model

    requests = []
    monkeypatch.setenv("OPENAI_API_KEY", "9router-scoring-key")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://9router.test/v1")
    get_settings.cache_clear()

    def respond(request):
        payload = json.loads(request.content)
        requests.append((str(request.url), request.headers["Authorization"], payload))
        return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "created": 1,
            "model": model, "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": '{"ok":true}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}})

    monkeypatch.setattr(gateway_model, "OpenAI", lambda **kwargs: OpenAI(
        **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))))
    monkeypatch.setattr(metrics, "wrap_openai", lambda client, **kwargs: client)
    adapter = metrics.judge("9router::" + model)
    result, cost = adapter.generate("Return ok=true as JSON.", Probe)
    assert result.ok is True and cost is None
    assert adapter.get_model_name() == model + " (9Router)"
    url, authorization, payload = requests[0]
    assert url == "https://9router.test/v1/chat/completions"
    assert authorization == "Bearer 9router-scoring-key"
    assert payload["model"] == model
    assert payload["response_format"]["type"] == "json_schema"
    assert "reasoning" not in payload and "provider" not in payload


@pytest.mark.parametrize(("model", "effort"), [
    ("deepseek/deepseek-v4.1-flash", "low"),
    ("z-ai/glm-5.3-flash", "low"),
    ("anthropic/claude-haiku-5.5", "low"),
    ("openai/gpt-4.1", "provider_default"),
])
def test_model_specific_reasoning_preserves_the_scoring_contract(model, effort):
    budget = 16384 if model == "deepseek/deepseek-v4.1-flash" else 4096
    assert metrics.judge_settings(model) == {
        "temperature": 0,
        "max_tokens": budget,
        "truncation_retry_max_tokens": budget * 2,
        "output_style": "compact-evidence-v1",
        "reasoning_effort": effort,
        "threshold": 0.7,
    }


def test_judge_allows_mandatory_reasoning_provider(monkeypatch):
    requests = []

    def create(**parameters):
        requests.append(parameters)
        if parameters.get("extra_body", {}).get("reasoning", {}).get("effort") == "none":
            raise BadRequestError("Reasoning is mandatory for this endpoint and cannot be disabled.", response=httpx.Response(400, request=httpx.Request("POST", "https://provider.invalid")), body={})
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))], usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5))

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(metrics.ProviderJudge, "load_model", lambda self, **kwargs: nullcontext(client))
    monkeypatch.setattr(metrics.ProviderJudge, "calculate_cost", lambda *args, **kwargs: 0)
    monkeypatch.setattr(metrics, "wrap_openai", lambda client, **kwargs: client)
    result, _ = metrics.judge("z-ai/glm-5.3-flash").generate("Return ok=true as JSON.", Probe)
    assert result.ok is True
    assert len(requests) == 1
    assert requests[0]["extra_body"]["reasoning"]["effort"] == "low"
    assert requests[0]["response_format"]["type"] == "json_schema"


def test_invalid_judge_configuration_is_not_retried_without_schema(monkeypatch):
    calls = []
    def create(**parameters):
        calls.append(parameters)
        raise BadRequestError("Unsupported parameters. Secret provider text must not be stored.", response=httpx.Response(400, request=httpx.Request("POST", "https://provider.invalid")), body={})
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(metrics.ProviderJudge, "load_model", lambda self, **kwargs: nullcontext(client))
    monkeypatch.setattr(metrics, "wrap_openai", lambda client, **kwargs: client)
    with pytest.raises(Exception) as caught:
        metrics.judge("z-ai/glm-5.3-flash").generate("Return JSON.", Probe)
    assert type(caught.value).__name__ == "JudgeConfigurationError"
    assert "Secret provider text" not in str(caught.value)
    assert len(calls) == 1


@pytest.mark.parametrize("model", ["deepseek/deepseek-v4.1-flash", "z-ai/glm-5.3-flash"])
def test_token_exhaustion_cannot_be_accepted_as_a_valid_judge_verdict(monkeypatch, model):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"claims":[]}'), finish_reason="length")])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response)))
    monkeypatch.setattr(metrics.ProviderJudge, "load_model", lambda self, **kwargs: nullcontext(client))
    monkeypatch.setattr(metrics, "wrap_openai", lambda client, **kwargs: client)
    metric = metrics.single_turn_metrics(judge_model=model)[0]
    scores = _metric_results(LLMTestCase(input="What is the deposit?", actual_output="60%.", retrieval_context=["The deposit is 60%."]), [metric])
    assert scores[0]["score"] is None
    assert scores[0]["passed"] is None
    assert scores[0]["error"] == "JudgeOutputError"
    assert scores[0]["failure_kind"] == "scoring"
    assert "output-token budget" in scores[0]["reason"]


@pytest.mark.parametrize(("model", "effort"), [
    ("deepseek/deepseek-v4.1-flash", "low"),
    ("z-ai/glm-5.3-flash", "low"),
    ("anthropic/claude-haiku-5.5", "low"),
    ("openai/gpt-4.1", None),
])
def test_truncated_output_retries_once_with_more_budget_and_the_same_schema(monkeypatch, model, effort):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'), finish_reason="length" if len(calls) == 1 else "stop")],usage=SimpleNamespace(prompt_tokens=10,completion_tokens=5))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(metrics.ProviderJudge, "load_model", lambda self, **kwargs: nullcontext(client))
    monkeypatch.setattr(metrics.ProviderJudge, "calculate_cost", lambda *args, **kwargs: 0)
    monkeypatch.setattr(metrics, "wrap_openai", lambda client, **kwargs: client)
    value, _ = metrics.judge(model).generate("Return JSON.", Probe)
    assert value.ok
    assert len(calls) == 2
    budget = 16384 if model == "deepseek/deepseek-v4.1-flash" else 4096
    assert [call["max_tokens"] for call in calls] == [budget, budget * 2]
    for call in calls:
        assert call["model"] == model
        assert call.get("extra_body", {}).get("reasoning", {}).get("effort") == effort
    assert calls[1]["response_format"] == calls[0]["response_format"]
