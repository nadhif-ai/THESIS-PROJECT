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


def test_answer_model_budget_and_reasoning_remain_provider_default(captured_client):
    models.get_llm("openai/gpt-6-luna")
    assert captured_client["max_tokens"] == 2048
    assert captured_client["extra_body"] is None
    assert captured_client["max_retries"] == 1


@pytest.fixture
def structured_provider(monkeypatch):
    state = SimpleNamespace(drip=False, requests=[], disconnected=threading.Event())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
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
                    "choices": [{"index": 0, "finish_reason": "stop", "message": {
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
            "provider": None, "model": "local/provider-model", "requests": 1,
        }
    assert len(structured_provider.requests) == 2
    for payload in structured_provider.requests:
        assert payload["model"] == "openai/gpt-oss-20b"
        assert payload["max_completion_tokens"] == 4096
        assert payload["reasoning"] == {"effort": "low"}
        assert payload["provider"] == {"require_parameters": True}
        assert payload["response_format"]["json_schema"]["strict"] is True


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
