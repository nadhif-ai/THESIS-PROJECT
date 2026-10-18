"""Keep the web application and durable consumer in the same Services build."""

import json
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_services_build_includes_python_subscriber_configuration():
    config = json.loads((ROOT / "vercel.json").read_text())
    python = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["vercel"]
    assert config["regions"] == ["bom1"]
    assert config["services"]["backend"]["entrypoint"] == "pyproject.toml"
    assert python["entrypoint"] == "app.main:app"
    assert {s["entrypoint"] for s in python["subscribers"]} == {"app.integrations.waha_queue"}


def test_authenticated_api_and_webhooks_route_before_frontend_catchall():
    config = json.loads((ROOT / "vercel.json").read_text())
    routes = config["rewrites"]
    assert routes[-1] == {"source": "/(.*)", "destination": {"service": "frontend"}}
    for path in ("/admin/api/(.*)", "/chat/(.*)", "/health"):
        assert next(r for r in routes if r["source"] == path)["destination"] == {"service": "backend"}
