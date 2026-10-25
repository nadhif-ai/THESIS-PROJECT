import requests

from app.admin import catalog, store
from app.integrations import waha
from testing.test_product_catalog import record


def prepared():
    catalog.save(record(), 0, 'operator')
    store.catalog_feature(True)
    store.enqueue_inbox('test','incoming','customer@c.us','Contoh roll up?')
    row = dict(store.claim_inbox('test'))
    selection = {k:record()[k] for k in ('asset_id','object_key','mime_type','caption','alt_text')}
    selection.update(revision=1, explicit=True)
    row.update(answer='Jawaban harga.', media_selection=selection, media_url=None)
    store.update_inbox('test','incoming',{'answer':row['answer'],'media_selection':selection},row['lease_token'])
    assert store.begin_inbox_send('test','incoming',row['lease_token'])
    return row


def test_image_first_failure_retains_text_and_no_replay(pg_live,monkeypatch):
    row = prepared()
    calls=[]
    def send(method,path,payload,**kwargs):
        calls.append((path,payload))
        if path.endswith('sendImage'):
            raise ValueError('Rejected')
        return {'id':str(len(calls))}
    monkeypatch.setattr(waha,'api',send)
    waha.send_reply(row)
    assert [p for p,_ in calls] == ['/api/sendImage','/api/sendText','/api/sendText']
    assert calls[1][1]['text']=='Jawaban harga.'
    saved=store.get_inbox('test','incoming')
    assert saved['delivery_parts']['text']['status']=='sent'
    assert saved['delivery_parts']['image']['status']=='failed'
    waha.send_reply(dict(saved))
    assert len(calls)==3


def test_image_and_text_timeouts_are_independent_and_not_replayed(pg_live,monkeypatch):
    row=prepared(); calls=[]
    def send(*args,**kwargs):
        calls.append(args[1]);raise requests.Timeout()
    monkeypatch.setattr(waha,'api',send)
    waha.send_reply(row)
    saved=store.get_inbox('test','incoming')
    assert saved['status']=='uncertain'
    assert saved['delivery_parts']['text']['status']=='uncertain'
    assert saved['delivery_parts']['image']['status']=='uncertain'
    waha.send_reply(dict(saved))
    assert calls==['/api/sendImage','/api/sendText']


def test_disable_before_dispatch_skips_image_but_keeps_details(pg_live,monkeypatch):
    row=prepared(); calls=[]
    catalog.set_enabled('roll-up-hero',False,1,'operator')
    def send(method,path,payload,**kwargs):
        calls.append(path)
        return {'id':'text-only'}
    monkeypatch.setattr(waha,'api',send)
    waha.send_reply(row)
    assert calls==['/api/sendText']
    saved=store.get_inbox('test','incoming')
    assert saved['delivery_parts']['image']['status']=='skipped'


def test_uncertain_image_suppresses_automatic_repeat(pg_live,monkeypatch):
    row=prepared()
    context=store.catalog_context('waha:test:customer@c.us')
    store.update_inbox('test','incoming',{'media_conversation_key':context['key'],'media_epoch':context['epoch']},row['lease_token'])
    def send(method,path,payload,**kwargs):
        if path.endswith('sendImage'):raise requests.Timeout()
        return {'id':'text'}
    monkeypatch.setattr(waha,'api',send)
    waha.send_reply(row)
    assert store.catalog_context(context['key'])['seen']==['roll-up-hero']
    assert store.catalog_context(context['key'],reset=True)['seen']==[]


def test_crash_between_send_and_checkpoint_expires_to_uncertain(pg_live):
    row=prepared()
    store.checkpoint_delivery_part(row,'text','sending')
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.whatsapp_inbox SET lease_expires_at=now()-interval '1 second'")
    assert store.claim_inbox('test') is None
    saved=store.get_inbox('test','incoming')
    assert saved['status']=='uncertain'
    assert saved['delivery_parts']['text']['status']=='uncertain'


def test_successful_image_is_not_replayed_after_text_timeout(pg_live,monkeypatch):
    row=prepared();calls=[]
    def send(method,path,payload,**kwargs):
        calls.append(path)
        if path.endswith('sendText'):raise requests.Timeout()
        return {'id':'image-accepted'}
    monkeypatch.setattr(waha,'api',send)
    waha.send_reply(row)
    saved=store.get_inbox('test','incoming')
    assert saved['delivery_parts']['image']['provider_id']=='image-accepted'
    assert saved['delivery_parts']['text']['status']=='uncertain'
    waha.send_reply(dict(saved))
    assert calls==['/api/sendImage','/api/sendText']


def test_text_failure_summary_remains_visible_after_successful_image(pg_live, monkeypatch):
    row = prepared()
    def send(method, path, payload, **kwargs):
        if path.endswith('sendText'):
            raise ValueError('Rejected')
        return {'id': 'accepted-image'}
    monkeypatch.setattr(waha, 'api', send)
    waha.send_reply(row)
    saved = store.get_inbox('test', 'incoming')
    assert saved['status'] == 'failed'
    assert 'text' in saved['error'].lower() and 'failed' in saved['error']


def test_old_automatic_selection_does_not_bypass_request_only_policy(pg_live, monkeypatch):
    row = prepared()
    row['body'] = 'Harga roll up?'
    row['media_selection']['explicit'] = False
    calls = []
    monkeypatch.setattr(waha, 'api', lambda method, path, payload, **kwargs: calls.append(path) or {'id': 'text'})
    waha.send_reply(row)
    assert calls == ['/api/sendText']


def test_legacy_suppression_does_not_erase_uncertain_image_checkpoint(pg_live, monkeypatch):
    row = prepared()
    store.checkpoint_delivery_part(row, 'image', 'uncertain', error='Uncertain legacy submission.')
    store.update_inbox('test','incoming',{'media_selection':None},row['lease_token'])
    row['media_selection'] = None
    row['media_url'] = 'https://example.com/old.png'
    calls=[]
    monkeypatch.setattr(waha,'api',lambda method,path,payload,**kw:calls.append(path) or {'id':'text'})
    waha.send_reply(row)
    assert calls == ['/api/sendText']
    assert store.get_inbox('test','incoming')['status'] == 'uncertain'
