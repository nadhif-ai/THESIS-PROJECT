"""Expired workers must be visible and recover without discarding evaluation scores."""

import pytest
from app.admin import kb_store, store


def abandoned(pg_live, environment='local', active=False, kind='evaluate'):
    with store._connection('execution') as db:
        kb_store._insert_job(db, 'abandoned', kind, {}, {'phase': 'scoring', 'result': {'cases': [{'id': 'saved'}]}})
        db.execute("UPDATE chatbot.jobs SET status='running' WHERE id='abandoned'")
        db.execute("UPDATE chatbot.admin_work SET environment=%s,lease_token='old',lease_until=now()+(%s)*interval '1 minute' WHERE job_id='abandoned'", (environment, 4 if active else -4))


def test_expired_evaluation_is_interrupted_in_both_read_shapes(pg_live):
    abandoned(pg_live)
    with store._connection() as db:
        summary = db.execute(f"SELECT {store._JOB_JSON} AS data FROM ({store._JOB_SUMMARY}) item WHERE id='abandoned'").fetchone()['data']
        detail = db.execute(f"SELECT {store._ADMIN_READS['job']} AS data", {'job_id': 'abandoned'}).fetchone()['data']
    for item in (summary, detail):
        assert item['status'] == 'interrupted'
        assert item['execution']['environment'] == 'local'
        assert item['resumable'] is True
        assert 'Resume' in item['dispatch_error']


def test_explicit_resume_can_move_expired_local_evaluation_to_production(pg_live, monkeypatch):
    abandoned(pg_live)
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('VERCEL_ENV', 'production')
    kb_store.retry('abandoned')
    row = kb_store.work('abandoned')
    assert row['environment'] == 'production'
    assert row['lease_token'] is None
    assert row['status'] == 'queued'
    assert row['sequence'] == 1
    assert row['checkpoint']['result']['cases'] == [{'id': 'saved'}]


@pytest.mark.parametrize('environment,active,kind', [('local', True, 'evaluate'), ('preview:other', False, 'evaluate'), ('local', False, 'sync')])
def test_resume_never_takes_live_or_preview_or_local_sync_work(pg_live, monkeypatch, environment, active, kind):
    abandoned(pg_live, environment, active, kind)
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('VERCEL_ENV', 'production')
    with pytest.raises(ValueError):
        kb_store.retry('abandoned')


def test_live_lease_is_not_reported_interrupted(pg_live):
    abandoned(pg_live, active=True)
    with store._connection() as db:
        item = db.execute(f"SELECT {store._JOB_JSON} AS data FROM ({store._JOB_SUMMARY}) item WHERE id='abandoned'").fetchone()['data']
    assert item['status'] == 'running'
    assert item['execution']['lease_active'] is True
    assert item['dispatch_error'] is None


def test_old_worker_cannot_checkpoint_after_takeover(pg_live, monkeypatch):
    abandoned(pg_live)
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('VERCEL_ENV', 'production')
    kb_store.retry('abandoned')
    with pytest.raises(RuntimeError, match='lease expired'):
        kb_store.checkpoint('abandoned', 'old', {}, {}, done=True)
    assert kb_store.work('abandoned')['checkpoint']['result']['cases'] == [{'id': 'saved'}]


def test_completed_evaluation_has_no_stall_or_resume_action(pg_live):
    abandoned(pg_live)
    with store._connection('execution') as db:
        db.execute("UPDATE chatbot.jobs SET status='completed' WHERE id='abandoned'")
        summary = db.execute(f"SELECT {store._JOB_JSON} AS data FROM ({store._JOB_SUMMARY}) item WHERE id='abandoned'").fetchone()['data']
        detail = db.execute(f"SELECT {store._ADMIN_READS['job']} AS data", {'job_id': 'abandoned'}).fetchone()['data']
    for item in (summary, detail):
        assert item['status'] == 'completed'
        assert item['execution']['stalled'] is False
        assert item['resumable'] is False
