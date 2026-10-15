import pytest
from fastapi.testclient import TestClient
from app.admin import store, knowledge


def seed_published():
    store.save_version({'id':'published','namespace':'retained','status':'ready','created_at':store.now(),'manifest':{},'records':[],'error':None})
    store.publish('published')


def test_startup_is_read_only(pg_live, monkeypatch):
    from app import dependencies
    seed_published()
    store.create_job_row('active','evaluate',{})
    store.set_job_state('active','running')
    monkeypatch.setattr(dependencies,'RAGChain',lambda: object())
    monkeypatch.setattr(knowledge,'bootstrap',lambda: pytest.fail('startup bootstrap'))
    dependencies.initialize_rag_system()
    assert store.list_job_rows()[0]['status']=='running'


def test_modes_and_first_write(pg_workspace):
    with pytest.raises(store.MaintenanceError):
        store.enqueue_inbox('s','closed','1@lid','body')
    with pg_workspace.admin_connection() as db:
        db.execute("UPDATE chatbot.runtime_control SET mode='intake',cutover_started_at='now' WHERE id=1")
    with pytest.raises(store.MaintenanceError):
        store.create_job_row('blocked','index',{})
    assert store.enqueue_inbox('s','accepted','1@lid','body')
    with pg_workspace.admin_connection() as db:
        marker=db.execute('SELECT first_live_write_at FROM chatbot.runtime_control').fetchone()[0]
        assert marker
    assert store.get_inbox('s','accepted')['status']=='queued'
    with pytest.raises(store.MaintenanceError):
        store.claim_inbox('s')


def test_missing_database_never_falls_back(tmp_path, monkeypatch):
    from app.config.settings import get_settings
    store.close_pool()
    monkeypatch.setenv('DATABASE_URL','')
    monkeypatch.setenv('DATA_DIR',str(tmp_path))
    get_settings.cache_clear()
    try:
        with pytest.raises(store.StateUnavailable,match='DATABASE_URL'):
            store.open_pool()
        assert not list(tmp_path.iterdir())
    finally:
        get_settings.cache_clear()


def test_privileged_role_rejected(pg_live, monkeypatch):
    from app.config.settings import get_settings
    seed_published()
    store.close_pool()
    monkeypatch.setenv('DATABASE_URL',pg_live.admin_dsn)
    get_settings.cache_clear()
    with pytest.raises(store.StateUnavailable,match='restricted'):
        store.check_ready()


def test_http_maintenance_is_sanitized_before_generation(pg_workspace, monkeypatch):
    from app.main import app
    from app import routes
    monkeypatch.setattr(routes,'_get_rag_chain',lambda: pytest.fail('model called in maintenance'))
    response=TestClient(app).post('/chat/faq',json={'session_id':'test','question':'hi'})
    assert response.status_code==503
    assert 'postgresql' not in response.text


def test_database_error_is_sanitized(pg_live):
    with pytest.raises(store.StateUnavailable) as error:
        with store._connection() as db:
            db.execute("SELECT 'secret-value'::integer")
    assert 'secret-value' not in str(error.value)


def test_synthetic_cutover_lifespan_and_reconciliation(source_snapshot,pg_workspace,monkeypatch):
    import time
    from app import dependencies
    from app.main import app
    from app.integrations import waha
    from scripts.migrate_state import snapshot,import_snapshot,verify_snapshot,set_runtime_mode,rollback_check
    from scripts.reconcile_waha import reconcile_messages,complete_reconciliation
    backup=pg_workspace.root/'backup.sqlite3'
    snapshot(source_snapshot,backup)
    import_snapshot(backup,pg_workspace.admin_dsn,'local-rehearsal')
    assert verify_snapshot(backup,pg_workspace.admin_dsn)['verified']
    monkeypatch.setattr(dependencies,'RAGChain',lambda:object())
    monkeypatch.setattr(waha,'start',lambda:None)
    monkeypatch.setattr(waha,'stop',lambda:None)
    monkeypatch.setattr(waha,'api',lambda *a,**k:pytest.fail('No provider calls in rehearsal'))
    from app.admin import jobs
    monkeypatch.setattr(jobs,'stop',lambda:None)
    with TestClient(app) as client:
        assert client.get('/health').status_code==200
        set_runtime_mode('intake',pg_workspace.admin_dsn)
        rows=[{'id':'maintenance-only','from':'123@lid','body':'synthetic','fromMe':False,'timestamp':time.time()}]
        assert reconcile_messages(rows,'asia-chatbot',True)['inserted']==1
        complete_reconciliation(rows,'asia-chatbot',0,time.time(),pg_workspace.admin_dsn)
        set_runtime_mode('live',pg_workspace.admin_dsn)
        assert not rollback_check(pg_workspace.admin_dsn)['allowed']
        assert len(store.conversations(channel='playground'))==1

from testing.test_state_migration import source_snapshot
