import json
import pytest
from app.admin import store
from scripts.reconcile_waha import scan_interval, reconcile_messages, complete_reconciliation
from scripts.migrate_state import import_snapshot, set_runtime_mode
from testing.test_state_migration import source_snapshot


def message(identifier='new', **fields):
    return {'id':identifier,'from':'123@lid','body':'new body','fromMe':False,'timestamp':100,**fields}


def test_scan_uses_closed_window_and_short_duplicate_pages(monkeypatch):
    monkeypatch.setenv('WAHA_SESSION','asia-chatbot')
    from app.config.settings import get_settings
    get_settings.cache_clear()
    seen=[]
    def request(method,path,payload=None,**kwargs):
        assert method=='GET';seen.append(path)
        if path.endswith('/chats?limit=100&offset=0'): return [{'id':'123@lid'}]
        if '/chats?' in path: return []
        if 'offset=0&' in path: return [message('one')]
        if 'offset=100&' in path: return [message('one'),message('two',timestamp=101)]
        return []
    rows=scan_interval(100,101,request)
    assert [r['id'] for r in rows]==['one','two']
    paths=[p for p in seen if '/messages?' in p]
    assert any('offset=200&' in p for p in paths)
    assert all('downloadMedia=false' in p and 'filter.timestamp.gte=99' in p and 'filter.timestamp.lte=102' in p for p in paths)


def test_replay_preserves_sent_uncertain_and_ack(source_snapshot,pg_workspace):
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    set_runtime_mode('intake',pg_workspace.admin_dsn)
    rows=[message('old',body='old body'),message(),message('reply-old',fromMe=True,ack=3)]
    assert reconcile_messages(rows,'asia-chatbot')['missing']==1
    summary=reconcile_messages(rows,'asia-chatbot',write=True)
    assert summary['inserted']==1
    assert store.get_inbox('asia-chatbot','old')['status']=='sent'
    assert store.get_inbox('asia-chatbot','old')['reply_ids']=='["reply-old"]'
    assert store.get_inbox('asia-chatbot','new')['sender']=='123@lid'
    assert reconcile_messages(rows,'asia-chatbot',write=True)['inserted']==0
    with pg_workspace.admin_connection() as db:
        assert db.execute("SELECT ack FROM chatbot.whatsapp_receipts WHERE message_id='reply-old'").fetchone()[0]==3
        db.execute("UPDATE chatbot.whatsapp_inbox SET status='uncertain' WHERE message_id='old'")
    reconcile_messages(rows,'asia-chatbot',write=True)
    assert store.get_inbox('asia-chatbot','old')['status']=='uncertain'


@pytest.mark.parametrize('bad',[message('old',body='conflict'),{'id':'malformed'},message('new',timestamp=float('nan'))])
def test_conflict_or_malformed_aborts_before_writes(source_snapshot,pg_workspace,bad):
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    set_runtime_mode('intake',pg_workspace.admin_dsn)
    with pytest.raises(ValueError):
        reconcile_messages([message('would-write'),bad],'asia-chatbot',write=True)
    assert store.get_inbox('asia-chatbot','would-write') is None


def test_scan_rejects_wrong_shape_and_infinite_pages():
    with pytest.raises(ValueError): scan_interval(1,2,lambda *a,**k:{'unexpected':[]})
    with pytest.raises(ValueError): scan_interval(1,2,lambda *a,**k:[{'id':'123@lid'}])


def test_replay_requires_intake_and_filters_noncustomers(pg_live):
    with pytest.raises(store.MaintenanceError): reconcile_messages([message()],'s',write=True)
    result=reconcile_messages([message(fromMe=True),message('group',**{'from':'1@g.us'}),message('empty',body='')],'s')
    assert result['eligible']==0


def test_completion_receipt_covers_window_and_dry_run_cannot_enable_live(source_snapshot,pg_workspace):
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    set_runtime_mode('intake',pg_workspace.admin_dsn)
    from datetime import datetime,timezone
    end=datetime.now(timezone.utc).timestamp()+1
    rows=[message(timestamp=end)]
    with pytest.raises(ValueError): set_runtime_mode('live',pg_workspace.admin_dsn)
    reconcile_messages(rows,'asia-chatbot',write=True)
    complete_reconciliation(rows,'asia-chatbot',0,end,pg_workspace.admin_dsn)
    set_runtime_mode('live',pg_workspace.admin_dsn)
    assert store.get_runtime_mode()=='live'


def test_new_chats_later_pages_and_out_of_window_are_handled():
    def request(method,path,payload=None,**kwargs):
        assert method=='GET'
        if '/messages?' not in path:
            if 'offset=0' in path: return [{'id':'1@lid'}]
            if 'offset=100' in path: return [{'id':'2@c.us'}]
            return []
        if 'offset=0&' not in path: return []
        if '1%40lid' in path: return [message('later',timestamp=101),message('older',timestamp=50)]
        return [message('new-chat',timestamp=99,**{'from':'2@c.us'})]
    rows=scan_interval(100,101,request)
    assert [r['id'] for r in rows]==['new-chat','later']


def test_conflicting_history_duplicates_refused():
    def request(method,path,payload=None,**kwargs):
        if '/messages?' not in path:
            return [{'id':'123@lid'}] if 'offset=0' in path else []
        if 'offset=0&' in path: return [message()]
        if 'offset=100&' in path: return [message(body='changed')]
        return []
    with pytest.raises(ValueError,match='Conflicting'):
        scan_interval(100,101,request)
