import psycopg
import pytest

from app.admin import store
from app.config.settings import get_settings


def test_external_runtime_pool_is_rejected_before_connect(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://chatbot_app@external.invalid/postgres"
    )
    get_settings.cache_clear()
    with pytest.raises(store.StateUnavailable, match="configuration"):
        store.open_pool()
    assert store._pool is None


def test_external_direct_sql_is_rejected_before_connect():
    with pytest.raises(psycopg.OperationalError, match="prohibit"):
        psycopg.connect("postgresql://postgres@external.invalid/postgres")
