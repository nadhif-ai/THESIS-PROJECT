import asyncio
import json
import threading
import time
from contextvars import ContextVar
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from app.backend import models


@pytest.fixture
def captured_client(monkeypatch):
    captured = {}
    monkeypatch.setattr(models, "get_settings", lambda: SimpleNamespace(
        openrouter_model="openai/gpt-6-luna", openrouter_api_key="test-key",
        openrouter_base_url="https://provider.test/api/v1",
    ))
    monkeypatch.setattr(models, "ChatOpenAI", lambda **kwargs: captured.update(kwargs) or object())
    models.get_llm.cache_clear()
    yield captured
    models.get_llm.cache_clear()


@pytest.mark.parametrize("model", ["openai/gpt-oss-20b", "z-ai/glm-5.3-flash"])
def test_structured_mandatory_reasoning_leaves_budget_for_json(captured_client, model):
    models.get_llm(model, structured=True, timeout=20)
    assert captured_client["extra_body"] == {
        "provider": {"require_parameters": True}, "reasoning": {"effort": "low"},
    }
    assert captured_client["max_tokens"] == 4096
    assert captured_client["request_timeout"] == 20
    assert captured_client["max_retries"] == 0


def test_unknown_structured_model_keeps_provider_parameters(captured_client):
    models.get_llm("vendor/other-model", structured=True)
    assert captured_client["extra_body"] == {"provider": {"require_parameters": True}}
    assert captured_client["max_tokens"] == 2048


def test_answer_budget_leaves_room_for_visible_output_without_hidden_retries(captured_client):
    models.get_llm("openai/gpt-6-luna")
    assert captured_client["max_tokens"] == 4096
    assert captured_client["extra_body"] is None
    assert captured_client["max_retries"] == 0


def test_current_anthropic_answer_model_bounds_reasoning(captured_client):
    models.get_llm('anthropic/claude-haiku-5.5')
    assert captured_client['max_tokens'] == 4096
    assert captured_client['extra_body'] == {'reasoning': {'effort': 'low'}}


@pytest.fixture
def structured_provider(monkeypatch):
    state = SimpleNamespace(drip=False, truncate_first=False, requests=[], authorizations=[], disconnected=threading.Event())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            state.authorizations.append(self.headers.get("Authorization"))
            state.requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                if state.drip:
                    for _ in range(30):
                        self.wfile.write(b" ")
                        self.wfile.flush()
                        time.sleep(0.025)
                self.wfile.write(json.dumps({
                    "id": "local-completion", "object": "chat.completion", "created": 1,
                    "model": "local/provider-model",
                    "choices": [{"index": 0, "finish_reason": "length" if state.truncate_first and len(state.requests) == 1 else "stop", "message": {
                        "role": "assistant", "content": '{"consistent":true}',
                    }}],
                    "usage": {"prompt_tokens": 11, "completion_tokens": 7,
                              "total_tokens": 18, "cost": 0.0002},
                }).encode())
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                state.disconnected.set()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(models, "get_settings", lambda: SimpleNamespace(
        openrouter_model="openai/gpt-6-luna", openrouter_api_key="local-test-key",
        openrouter_base_url=f"http://127.0.0.1:{server.server_port}/v1",
    ))
    models.get_llm.cache_clear()
    yield state
    models.get_llm.cache_clear()
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


CONSISTENCY_SCHEMA = {
    "title": "Consistency", "description": "Attachment consistency decision",
    "type": "object", "properties": {"consistent": {"type": "boolean"}},
    "required": ["consistent"], "additionalProperties": False,
}


def call_structured(timeout=2):
    return models.structured_response(
        CONSISTENCY_SCHEMA, [("user", "Check consistency")],
        timeout=timeout, model="openai/gpt-oss-20b",
    )


def test_structured_deadline_cancels_http_200_body_that_keeps_arriving(structured_provider):
    structured_provider.drip = True
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        call_structured(timeout=0.15)
    assert time.monotonic() - started < 0.65
    assert structured_provider.disconnected.wait(timeout=0.4)
    assert len(structured_provider.requests) == 1


def test_structured_calls_across_new_loops_preserve_payload_and_usage(structured_provider):
    for _ in range(2):
        parsed, usage = call_structured()
        assert parsed == {"consistent": True}
        assert usage == {
            "prompt_tokens": 11, "completion_tokens": 7, "cost_usd": 0.0002,
            "provider": "openrouter", "model": "local/provider-model", "requests": 1,
        }
    assert len(structured_provider.requests) == 2
    for payload in structured_provider.requests:
        assert payload["model"] == "openai/gpt-oss-20b"
        assert payload["max_completion_tokens"] == 4096
        assert payload["reasoning"] == {"effort": "low"}
        assert payload["provider"] == {"require_parameters": True}
        assert payload["response_format"]["json_schema"]["strict"] is True


def test_answer_recovery_sends_larger_budget_through_actual_http_client(structured_provider):
    from app.backend.answer_generation import generate
    from langchain_core.messages import HumanMessage

    structured_provider.truncate_first = True
    result = generate(models.get_llm('openai/gpt-6-luna'), [HumanMessage(content='Harga?')])
    assert result['recovery'] == 'regenerated'
    assert result['usage']['requests'] == 2
    assert result['usage']['completion_tokens'] == 14
    assert result['usage']['cost_usd'] == .0004
    assert [request['max_completion_tokens'] for request in structured_provider.requests] == [4096, 8192]


@pytest.mark.parametrize("selected", ["azure/gpt-5.6-terra-20260709-global", "azure/gpt-5.6-luna-20260709-global", "cx/gpt-6-luna[1m]", "glm/glm-5.3-flash"])
def test_9router_intent_uses_its_endpoint_key_and_structured_schema(structured_provider, monkeypatch, selected):
    settings = models.get_settings()
    settings.openai_api_key = "9router-only-key"
    settings.openai_endpoint = settings.openrouter_base_url
    monkeypatch.setattr(models, "get_settings", lambda: settings)
    models.get_llm.cache_clear()
    result, usage = models.structured_response(CONSISTENCY_SCHEMA, [("user", "Check consistency")],
                                               timeout=2, model="9router::" + selected)
    assert result == {"consistent": True}
    assert usage["provider"] == "9router"
    assert structured_provider.authorizations == ["Bearer 9router-only-key"]
    payload = structured_provider.requests[0]
    assert payload["model"] == selected
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert "provider" not in payload and "reasoning" not in payload


def test_structured_deadline_inside_running_loop_keeps_context_and_closes_io(
    structured_provider, monkeypatch,
):
    marker = ContextVar("structured_test_marker", default=None)
    marker.set("parent-trace-context")
    observed = []
    original = models.AsyncOpenAI

    def capture_client(**kwargs):
        observed.append(marker.get())
        return original(**kwargs)

    monkeypatch.setattr(models, "AsyncOpenAI", capture_client)
    structured_provider.drip = True

    async def caller():
        with pytest.raises(TimeoutError):
            call_structured(timeout=0.15)

    asyncio.run(caller())
    assert observed == ["parent-trace-context"]
    assert structured_provider.disconnected.wait(timeout=0.4)
    assert len(structured_provider.requests) == 1
