"""Public frontend routes must not weaken the administration API boundary."""

from fastapi.testclient import TestClient
import pytest

from app.admin import routes, store
from app.config.settings import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def administration_state(pg_live):
    yield


def test_landing_and_login_share_the_frontend_without_exposing_api(tmp_path, monkeypatch):
    index = tmp_path / "index.html"
    index.write_text('<html lang="en"><div id="root"></div></html>')
    monkeypatch.setattr(routes, "FRONTEND_INDEX", index)
    client = TestClient(app)

    for path in ("/", "/admin/", "/admin/login"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert response.text == index.read_text()
        assert "location" not in response.headers

    assert client.get("/admin/api/me").status_code == 401
    assert client.get("/admin/api/overview").status_code == 401
    assert client.get("/admin/api/not-a-route").status_code == 404


def test_unbuilt_frontend_reports_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(routes, "FRONTEND_INDEX", tmp_path / "missing.html")
    client = TestClient(app)
    assert client.get("/").status_code == 503
    assert client.get("/admin/login").status_code == 503
