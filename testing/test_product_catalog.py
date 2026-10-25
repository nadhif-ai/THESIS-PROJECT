def semantic(monkeypatch, action='show', product='roll-up-banner'):
    from app.backend import product_intent
    value = product_intent.ProductIntent(action=action, product_ids=[product], view='hero',
        attributes=[], exact_visual=False, resolution='resolved', clarification='', changes_product=True)
    monkeypatch.setattr(product_intent, 'extract', lambda *a, **kw: value)


import pytest

from app.admin import catalog


def record():
    return {
        'asset_id': 'roll-up-hero', 'category_id': 'standing-banner',
        'product_type': 'roll-up-banner', 'covered_product_types': ['roll-up-banner'],
        'role': 'hero', 'aliases': ['roll up', 'rollup'],
        'description': 'Ilustrasi roll up banner', 'alt_text': 'Roll up banner',
        'caption': 'Ilustrasi roll up banner.', 'depicted_variants': [],
        'source_only_variants': [], 'retrieval_keywords': [], 'negative_retrieval_keywords': [],
        'object_key': 'roll-up-hero/' + 'a'*64 + '.png',
        'mime_type': 'image/png', 'width': 1200, 'height': 1200,
        'sha256': 'a'*64, 'size_bytes': 100, 'is_ai_generated': True,
        'provenance': {}, 'enabled': True,
    }


def test_save_activates_and_stale_save_preserves_current_asset(pg_live):
    initial = catalog.save(record(), expected_revision=0, approved_by='operator')
    assert initial['revision'] == 1
    assert catalog.snapshot()['assets'][0]['asset_id'] == 'roll-up-hero'
    replacement = dict(record(), caption='Contoh ilustrasi roll up.')
    assert catalog.save(replacement, expected_revision=1, approved_by='operator')['revision'] == 2
    with pytest.raises(catalog.Conflict):
        catalog.save(record(), expected_revision=1, approved_by='operator')
    assert catalog.snapshot()['assets'][0]['caption'] == replacement['caption']


def test_disable_and_export_do_not_touch_knowledge(pg_live):
    catalog.save(record(), expected_revision=0, approved_by='operator')
    before = catalog.snapshot()['revision']
    catalog.set_enabled('roll-up-hero', False, 1, 'operator')
    data = catalog.snapshot()
    assert data['revision'] > before
    assert data['assets'][0]['enabled'] is False
    assert catalog.asset_enabled('roll-up-hero') is False


def test_replacement_decode_failure_preserves_active_record(pg_live, monkeypatch):
    from app.admin import catalog_storage
    catalog.save(record(), 0, 'operator')
    with pytest.raises(ValueError):
        catalog_storage.inspect(b'not an image')
    assert catalog.snapshot()['assets'][0]['revision'] == 1


def test_catalog_api_is_authenticated_and_rejects_stale_save(pg_live):
    from testing.test_prompt_settings import client, authorize
    with client() as browser:
        assert browser.get('/admin/api/catalog').status_code == 401
        authorize(browser)
        catalog.save(record(), 0, 'operator')
        asset = browser.get('/admin/api/catalog').json()['assets'][0]
        fields = {k:asset[k] for k in catalog.AssetEdit.model_fields}
        result = browser.put('/admin/api/catalog/assets/roll-up-hero', json={**fields,'expected_revision':1})
        assert result.status_code == 200
        assert browser.put('/admin/api/catalog/assets/roll-up-hero', json={**fields,'expected_revision':1}).status_code == 409
        assert browser.get('/admin/api/catalog/export').json()['assets'][0]['revision'] == 2
        browser.headers['X-CSRF-Token'] = 'invalid'
        assert browser.put('/admin/api/catalog/feature', json={'enabled':True}).status_code == 403


def test_24_hour_inactivity_and_reset_clear_focus_and_attempt_boundary(pg_live):
    from app.admin import store
    first = store.catalog_context('waha:test:customer')
    store.catalog_focus(first,['roll-up-banner'])
    assert store.catalog_context('waha:test:customer')['focus'] == ['roll-up-banner']
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.catalog_conversations SET last_activity=now()-interval '25 hours'")
    expired = store.catalog_context('waha:test:customer')
    assert expired['epoch'] != first['epoch'] and expired['focus'] == []
    reset = store.catalog_context('waha:test:customer', reset=True)
    assert reset['epoch'] != expired['epoch']


def test_import_maps_all_27_approved_assets_and_preserves_dashboard_edits(pg_live,monkeypatch):
    from app.admin import catalog_import, catalog_storage
    original = catalog_storage.inspect
    def publish(identifier,content):
        info=original(content)
        return {**info,'object_key':identifier+'/'+info['sha256']+('.png' if info['mime_type']=='image/png' else '.jpg')}
    monkeypatch.setattr(catalog_storage,'publish',publish)
    first=catalog_import.import_manifest('dataset/image-product/manifest.json','user-Q3')
    assert len(first['imported']) == 27
    current=catalog.snapshot()
    assert len(current['assets'])==27 and len({a['category_id'] for a in current['assets']})==7
    asset=current['assets'][0]
    catalog.save({**asset,'caption':'Reviewed dashboard caption.'},asset['revision'],'operator')
    second=catalog_import.import_manifest('dataset/image-product/manifest.json','user-Q3')
    assert second['imported']==[] and len(second['preserved'])==27
    assert catalog.snapshot()['assets'][0]['caption']=='Reviewed dashboard caption.'


def test_shared_rag_preview_selects_catalog_not_legacy_url_and_honors_topic_context(pg_live,monkeypatch):
    from types import SimpleNamespace
    from langchain_core.documents import Document
    from app.backend import chain,vectorstore
    from app.admin import store
    from testing.test_global_knowledge import seed_active
    seed_active()
    catalog.save(record(),0,'operator');store.catalog_feature(True)
    monkeypatch.setattr(chain,'get_llm',lambda *args:SimpleNamespace(invoke=lambda messages:SimpleNamespace(content='Jawaban dari knowledge.')))
    searches=[]
    def retrieve(**kwargs):
        searches.append(kwargs['query'])
        return [(Document(page_content='Roll up banner tersedia.',metadata={'source':'products.txt','media_url':'https://unapproved.example/other.png'}),0.1)]
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',retrieve)
    rag=chain.RAGChain()
    semantic(monkeypatch)
    first=rag.run('Gambar roll up banner?', 'preview', channel='playground')
    assert first.media_selection['asset_id']=='roll-up-hero'
    assert 'unapproved.example' not in first.media_url
    semantic(monkeypatch, 'none')
    followup=rag.run('Kalau 5 pcs?', 'preview',channel='playground')
    assert followup.media_selection is None
    assert followup.media_decision['reason']=='image_not_requested'
    semantic(monkeypatch, 'none', 'x-banner')
    other=rag.run('Harga X-banner?', 'preview',channel='playground')
    assert searches[-1]=='Harga X-banner?\nProduk yang dimaksud: x banner'
    assert other.media_decision['reason']=='image_not_requested'
    context=store.catalog_context('playground:preview')
    assert context['seen']==['roll-up-hero']
    reset=rag.run('reset','preview',channel='playground')
    assert reset.media_selection is None
    assert store.catalog_context('playground:preview')['focus']==[]


def test_preview_attempts_are_isolated_and_suppressed_on_return(pg_live):
    from app.admin import store
    preview=store.catalog_context('playground:operator')
    store.catalog_focus(preview,['roll-up-banner'],preview_asset=record())
    store.catalog_focus(preview,['stempel'])
    assert store.catalog_context('playground:operator')['seen']==['roll-up-hero']
    assert store.catalog_context('waha:account:customer')['seen']==[]
    assert store.catalog_context('playground:operator',reset=True)['seen']==[]


def test_focus_and_generated_choice_are_persisted_together_under_inbox_lease(pg_live):
    from app.admin import store
    context=store.catalog_context('waha:account:customer')
    store.enqueue_inbox('account','message','customer','Harga roll up?')
    row=store.claim_inbox('account')
    assert store.catalog_context(context['key'])['focus']==[]
    store.update_inbox('account','message',{'answer':'Harga dari knowledge.','media_selection':{'asset_id':'roll-up-hero'},
        'media_conversation_key':context['key'],'media_epoch':context['epoch'],'media_focus':['roll-up-banner']},row['lease_token'])
    assert store.get_inbox('account','message')['media_selection']['asset_id']=='roll-up-hero'
    assert store.catalog_context(context['key'])['focus']==['roll-up-banner']


def test_enabling_media_preserves_established_factual_conversation(pg_live,monkeypatch):
    from types import SimpleNamespace
    from langchain_core.documents import Document
    from app.backend import chain,vectorstore
    from app.admin import store
    from testing.test_global_knowledge import seed_active
    seed_active();catalog.save(record(),0,'operator')
    store.record_conversation('existing','whatsapp','Saya mau roll up banner.','Baik Kak, roll up banner.')
    store.catalog_feature(True)
    prompts=[]
    monkeypatch.setattr(chain,'get_llm',lambda *args:SimpleNamespace(invoke=lambda messages:(prompts.append(messages) or SimpleNamespace(content='Jawaban untuk 5 pcs.'))))
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',lambda **kwargs:[(Document(page_content='Roll up banner tersedia.',metadata={}),0.1)])
    chain.RAGChain().run('Kalau 5 pcs?', 'existing',channel='whatsapp')
    assert any('Saya mau roll up' in message.content for message in prompts[0])


def test_authenticated_playground_coordinates_visual_status_with_factual_details(pg_live, monkeypatch):
    from types import SimpleNamespace
    from langchain_core.documents import Document
    from app import dependencies
    from app.backend import chain, vectorstore
    from app.admin import store
    from testing.test_global_knowledge import seed_active
    from testing.test_prompt_settings import client, authorize
    seed_active(); catalog.save({**record(), 'description': 'UNTRUSTED_CATALOG_PRICE Rp 1'}, 0, 'operator')
    store.catalog_feature(True)
    semantic(monkeypatch)
    captured = []
    def invoke(messages):
        captured.append(messages)
        return SimpleNamespace(content='Ilustrasi roll up, Kak. Harga bahan A Rp 50.000; bahan B Rp 60.000. Mau bahan yang mana?')
    monkeypatch.setattr(chain, 'get_llm', lambda *args: SimpleNamespace(invoke=invoke))
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', lambda **kwargs: [
        (Document(page_content='Roll up banner: bahan A Rp 50.000; bahan B Rp 60.000.', metadata={}), 0.1)])
    monkeypatch.setattr(dependencies, 'get_rag_chain', lambda: chain.RAGChain())
    with client() as browser:
        authorize(browser)
        result = browser.post('/admin/api/playground', json={'question': 'Preview roll up dong', 'session_id': 'visual'} )
        assert result.status_code == 200
        data = result.json()
        assert data['media_selection']['asset_id'] == 'roll-up-hero'
        assert 'Rp 50.000' in data['answer'] and 'Rp 60.000' in data['answer']
        prompt = '\n'.join(m.content for m in captured[-1])
        assert 'Ilustrasi katalog terpilih: roll up' in prompt
        assert 'Rp 50.000' in prompt and 'UNTRUSTED_CATALOG_PRICE' not in prompt
        assert 'gambar dahulu' in prompt and 'pesan terpisah' in prompt
        again = browser.post('/admin/api/playground', json={'question': 'Kirim itu lagi', 'session_id': 'visual'}).json()
        assert again['media_selection']['asset_id'] == 'roll-up-hero'


def test_generation_failure_suppresses_selected_image_and_focus(pg_live, monkeypatch):
    from types import SimpleNamespace
    from langchain_core.documents import Document
    from app.backend import chain, vectorstore
    from app.admin import store
    from testing.test_global_knowledge import seed_active
    seed_active(); catalog.save(record(), 0, 'operator'); store.catalog_feature(True)
    semantic(monkeypatch)
    def fail(messages):
        raise RuntimeError('Simulated provider failure')
    monkeypatch.setattr(chain, 'get_llm', lambda *args: SimpleNamespace(invoke=fail))
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', lambda **kwargs: [
        (Document(page_content='Roll up banner tersedia.', metadata={}), 0.1)])
    result = chain.RAGChain().run('Gambar roll up', 'failed-preview', channel='playground')
    assert result.error and result.media_selection is None and result.media_url is None
    assert result.media_decision['reason'] == 'generation_error'
    assert store.catalog_context('playground:failed-preview')['focus'] == []


def test_legacy_media_fallback_is_request_only_in_shared_rag(pg_live, monkeypatch):
    from types import SimpleNamespace
    from langchain_core.documents import Document
    from app.backend import chain, vectorstore
    from testing.test_global_knowledge import seed_active
    seed_active()
    monkeypatch.setattr(chain, 'get_llm', lambda *args: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content='Harga mengikuti pilihan bahan.')))
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', lambda **kwargs: [
        (Document(page_content='Roll up banner tersedia.', metadata={'media_url': 'https://example.com/roll-up.png'}), .1)])
    rag = chain.RAGChain()
    assert rag.run('Harga roll up?', 'legacy', channel='playground').media_url is None
    semantic(monkeypatch)
    assert rag.run('Kirim gambarnya', 'legacy', channel='playground').media_url == 'https://example.com/roll-up.png'


def test_visual_attribute_backfill_preserves_dashboard_edits_and_replaced_images(pg_live, monkeypatch):
    from app.admin import catalog_import, catalog_storage, store
    from pathlib import Path
    import json
    seed = next(a for a in json.loads(Path('dataset/image-product/manifest.json').read_text())['assets']
                if a['id'] == 'kartu-nama-glossy-doff-comparison')
    asset = {**record(), 'asset_id':seed['id'], 'category_id':'id-card-kartu-nama',
             'product_type':'kartu-nama', 'covered_product_types':['kartu-nama'],
             'role':seed['role'], 'sha256':seed['image']['sha256'],
             'object_key':seed['id']+'/'+seed['image']['sha256']+'.png',
             'caption':'Reviewed caption.'}
    catalog.save(asset, 0, 'operator')
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.catalog_assets SET metadata=metadata-'visual_attributes'")
    result = catalog_import.backfill_visual_attributes('dataset/image-product/manifest.json','operator')
    assert result['updated'] == [seed['id']]
    saved = catalog.snapshot()['assets'][0]
    assert saved['visual_attributes'] == {'finish':['glossy','doff']}
    assert saved['caption'] == 'Reviewed caption.'
    assert catalog_import.backfill_visual_attributes('dataset/image-product/manifest.json','operator')['updated'] == []
    edited = catalog.save({**saved,'visual_attributes':{'finish':[' Glossy ', 'glossy']}}, saved['revision'],'operator')
    assert edited['visual_attributes'] == {'finish':['glossy']}
    assert catalog_import.backfill_visual_attributes('dataset/image-product/manifest.json','operator')['updated'] == []
