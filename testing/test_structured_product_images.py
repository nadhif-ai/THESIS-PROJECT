from types import SimpleNamespace

import pytest
from app.backend.product_intent import extract as real_extract

from langchain_core.documents import Document

from app.admin import catalog, store
from app.backend import chain, vectorstore
from testing.test_global_knowledge import seed_active
from testing.test_product_catalog import record
from testing.test_prompt_settings import client, authorize


@pytest.mark.parametrize("resolution", ["unsupported", "ambiguous"])
def test_nonvisual_questions_do_not_inherit_image_unavailability_text(pg_live, monkeypatch, resolution):
    from app.backend import product_intent, attachment_answer
    seed_active()
    intent = product_intent.ProductIntent(action='none', product_ids=[], view='hero', attributes=[],
        exact_visual=False, resolution=resolution, clarification='', changes_product=False)
    monkeypatch.setattr(product_intent, 'extract', lambda *args, **kwargs: intent)
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', lambda **kwargs: [])
    monkeypatch.setattr(chain, 'get_llm', lambda *args: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content='Jawaban informasi toko.')))
    monkeypatch.setattr(attachment_answer, 'consistent', lambda *args, **kwargs: pytest.fail('A nonvisual answer must not enter attachment validation'))
    result = chain.RAGChain().run('Apa informasi toko ini?', 'ordinary-question', channel='playground')
    assert result.answer == 'Jawaban informasi toko.'
    assert result.media_url is None


@pytest.mark.parametrize("channel", ["evaluation", "playground"])
@pytest.mark.parametrize("question, answer", [
    ("Di mana alamat gerai Pamulang?", "Gerai Pamulang berada di Jl. Pajajaran No. 38."),
    ("Berapa uang muka minimum sebelum dicetak?", "Uang muka minimum adalah 60% sebelum berkas masuk antrean cetak."),
])
def test_failed_intent_preserves_factual_answer_without_publishing_image_status(pg_live, monkeypatch, channel, question, answer):
    from app.backend import product_intent, attachment_answer

    seed_active()
    monkeypatch.setattr(product_intent, "structured_response", lambda *args, **kwargs: ({
        "action": "none", "product_ids": [], "view": "hero", "attributes": [],
        "exact_visual": False, "resolution": "failed", "clarification": "",
        "changes_product": False,
    }, {}))
    monkeypatch.setattr(product_intent, "extract", real_extract)
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", lambda **kwargs: [
        (Document(page_content=answer, metadata={"source": "sop.txt"}), .1)])
    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(content=answer)))
    guarded = []

    def check(text, **kwargs):
        guarded.append((text, kwargs))
        return False

    monkeypatch.setattr(attachment_answer, "consistent", check)
    result = chain.RAGChain().run(question, "failed-factual-intent", channel=channel)

    assert guarded == []
    assert result.media_url is None and result.media_selection is None
    assert result.media_decision["intent_resolution"] == "ambiguous"
    assert "answer_validation" not in result.media_decision
    assert result.answer == answer


def test_provider_schema_reserves_failed_resolution_for_application(monkeypatch):
    from app.backend import product_intent

    sent = []

    def provider(schema, *args, **kwargs):
        sent.append(schema)
        return {"action": "none", "product_ids": [], "view": "hero", "attributes": [],
                "exact_visual": False, "resolution": "unsupported", "clarification": "",
                "changes_product": False}, {}

    monkeypatch.setattr(product_intent, "structured_response", provider)
    intent = real_extract("Berapa jam layanan toko?", [])

    assert intent.action == "none" and intent.resolution == "unsupported"
    assert "failed" not in sent[0]["properties"]["resolution"]["enum"]
    assert product_intent.failed_intent().resolution == "failed"
    assert "failed" in product_intent.ProductIntent.model_json_schema()["properties"]["resolution"]["enum"]


def test_provider_failed_visual_intent_remains_ambiguous_and_guarded(pg_live, monkeypatch):
    from app.backend import product_intent, attachment_answer

    seed_active()
    catalog.save(record(), 0, "operator")
    store.catalog_feature(True)
    monkeypatch.setattr(product_intent, "structured_response", lambda *args, **kwargs: ({
        "action": "show", "product_ids": ["roll-up-banner"], "view": "hero", "attributes": [],
        "exact_visual": False, "resolution": "failed", "clarification": "Produk yang mana, Kak?",
        "changes_product": False,
    }, {}))
    monkeypatch.setattr(product_intent, "extract", real_extract)
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", lambda **kwargs: [])
    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace(invoke=lambda messages:
        SimpleNamespace(content="Foto sudah saya kirim: https://invented.example/photo.png")))
    guarded = []

    def check(text, **kwargs):
        guarded.append(kwargs)
        return False

    monkeypatch.setattr(attachment_answer, "consistent", check)
    result = chain.RAGChain().run("Boleh lihat foto roll up?", "provider-failed-visual", channel="playground")

    assert len(guarded) == 1 and guarded[0]["selected"] is False
    assert result.media_decision["intent_resolution"] == "ambiguous"
    assert result.media_decision["reason"] == "intent_ambiguous"
    assert result.media_decision["answer_validation"] == "safe_fallback"
    assert result.media_url is None and result.media_selection is None
    assert "invented.example" not in result.answer and "sudah saya kirim" not in result.answer


@pytest.mark.parametrize("empty", [False, True])
def test_playground_uses_semantic_product_identity_without_factual_name_gate(pg_live, monkeypatch, empty):
    from app import dependencies
    from app.backend import product_intent
    seed_active(empty=empty)
    catalog.save({**record(), 'asset_id': 'plakat-hero', 'category_id': 'other-physical-printing', 'product_type': 'plakat-akrilik',
                  'covered_product_types': ['plakat-akrilik'], 'object_key': 'plakat-hero/' + 'a'*64 + '.png', 'aliases': []}, 0, 'operator')
    store.catalog_feature(True)
    intent = product_intent.ProductIntent(action='show', product_ids=['plakat-akrilik'],
        view='hero', attributes=[], exact_visual=False, resolution='resolved',
        clarification='', changes_product=True)
    monkeypatch.setattr(product_intent, 'extract', lambda *a, **kw: intent)
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', lambda **kw: [
        (Document(page_content='Harga perlu dikonfirmasi sesuai pesanan.', metadata={}), .1)])
    monkeypatch.setattr(chain, 'get_llm', lambda *a: SimpleNamespace(invoke=lambda messages:
        SimpleNamespace(content='Harga perlu dikonfirmasi sesuai pesanan.')))
    monkeypatch.setattr(dependencies, 'get_rag_chain', lambda: chain.RAGChain())
    with client() as browser:
        authorize(browser)
        response = browser.post('/admin/api/playground', json={
            'question': 'Hi admin kirimin foto preview plakat akrilik dong', 'session_id': 'plakat'})
        assert response.status_code == 200
        data = response.json()
        assert data['media_selection']['asset_id'] == 'plakat-hero'
        assert data['media_decision']['product_ids'] == ['plakat-akrilik']


def test_requested_size_keeps_single_product_hero_and_extraction_failure_keeps_focus(pg_live, monkeypatch):
    from app.backend import product_intent
    seed_active()
    base = {**record(), 'asset_id': 'x-hero', 'object_key': 'x-hero/'+'a'*64+'.png',
            'product_type': 'x-banner', 'covered_product_types': ['x-banner'], 'aliases': []}
    catalog.save(base, 0, 'operator')
    catalog.save({**base, 'asset_id': 'stands', 'object_key': 'stands/'+'a'*64+'.png',
        'role': 'form_comparison', 'covered_product_types': ['x-banner','y-banner','roll-up-banner']}, 0, 'operator')
    store.catalog_feature(True)
    requested = product_intent.ProductIntent(action='show', product_ids=['x-banner'], view='hero',
        attributes=[{'name':'size','value':'60 x 160 cm','evidence':'60 x 160 cm'}],
        exact_visual=False, resolution='resolved', clarification='', changes_product=True)
    monkeypatch.setattr(product_intent,'extract',lambda *a,**kw:requested)
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',lambda **kw:[])
    monkeypatch.setattr(chain,'get_llm',lambda *a:SimpleNamespace(invoke=lambda messages:SimpleNamespace(content='Konfirmasi harga ke admin, Kak.')))
    rag=chain.RAGChain()
    first=rag.run('Kirimin foto X-banner 60 x 160 cm', 'size', channel='playground')
    assert first.media_selection['asset_id']=='x-hero'
    monkeypatch.setattr(product_intent,'extract',lambda *a,**kw:product_intent.failed_intent())
    failed=rag.run('Boleh liat yang satunya?', 'size', channel='playground')
    assert failed.media_selection is None
    assert failed.media_decision['reason']=='intent_failed'
    assert store.catalog_context('playground:size')['focus']==['x-banner']


def test_contradictory_detail_text_never_reaches_customer_with_selected_image(pg_live, monkeypatch):
    from app.backend import product_intent, attachment_answer
    seed_active(); catalog.save(record(),0,'operator'); store.catalog_feature(True)
    intent=product_intent.ProductIntent(action='show',product_ids=['roll-up-banner'],view='hero',attributes=[],
        exact_visual=False,resolution='resolved',clarification='',changes_product=True)
    monkeypatch.setattr(product_intent,'extract',lambda *a,**kw:intent)
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',lambda **kw:[])
    monkeypatch.setattr(chain,'get_llm',lambda *a:SimpleNamespace(invoke=lambda messages:
        SimpleNamespace(content='Maaf, tautan foto roll up belum tersedia.')))
    monkeypatch.setattr(attachment_answer,'consistent',lambda *a,**kw:False)
    response=chain.RAGChain().run('Kirim gambar roll up','contradiction',channel='playground')
    assert response.media_selection['asset_id']=='roll-up-hero'
    assert 'tautan foto' not in response.answer
    assert 'Ini ilustrasi' in response.answer
    assert response.media_decision['answer_validation']=='safe_fallback'


def test_empty_knowledge_with_catalog_preserves_controlled_factual_answer(pg_live, monkeypatch):
    from app.admin.global_knowledge import EMPTY_ANSWER
    seed_active(empty=True); catalog.save(record(), 0, 'operator'); store.catalog_feature(True)
    def unexpected(*a, **kw):
        raise AssertionError('Empty factual knowledge must not call a provider')
    monkeypatch.setattr(chain, 'get_llm', lambda *a: SimpleNamespace(invoke=unexpected))
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', unexpected)
    response = chain.RAGChain().run('Harga roll up?', 'empty', channel='playground')
    assert response.answer == EMPTY_ANSWER and response.media_selection is None


def test_catalog_intent_excludes_conversation_older_than_24_hours(pg_live, monkeypatch):
    from app.backend import product_intent
    seed_active(); catalog.save(record(), 0, 'operator'); store.catalog_feature(True)
    store.record_conversation('expired', 'playground', 'Kirim foto roll up', 'Ini ilustrasi roll up.')
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.conversations SET created_at=(now()-interval '25 hours')::text")
    seen = []
    def extract(question, history, focus, **kwargs):
        seen.extend(history)
        return product_intent.failed_intent()
    monkeypatch.setattr(product_intent, 'extract', extract)
    monkeypatch.setattr(vectorstore, 'similarity_search_with_score', lambda **kw: [])
    monkeypatch.setattr(chain, 'get_llm', lambda *a: SimpleNamespace(invoke=lambda m: SimpleNamespace(content='Produk mana, Kak?')))
    response = chain.RAGChain().run('Kirim itu lagi', 'expired', channel='playground')
    assert not seen and response.media_selection is None


def test_waha_worker_pins_shared_semantic_result_and_sends_image_then_details(pg_live, monkeypatch):
    from app import dependencies
    from app.backend import product_intent
    from app.integrations import waha
    seed_active(); catalog.save(record(), 0, 'operator'); store.catalog_feature(True)
    request = product_intent.ProductIntent(action='show',product_ids=['roll-up-banner'],view='hero',attributes=[],
        exact_visual=False,resolution='resolved',clarification='',changes_product=True)
    monkeypatch.setattr(product_intent,'extract',lambda *a,**kw:request)
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',lambda **kw:[
        (Document(page_content='Roll up Rp 195.000.', metadata={}), .1)])
    monkeypatch.setattr(chain,'get_llm',lambda *a:SimpleNamespace(invoke=lambda m:SimpleNamespace(content='Roll up Rp 195.000.')))
    monkeypatch.setattr(dependencies,'get_rag_chain',lambda:chain.RAGChain())
    calls=[]
    monkeypatch.setattr(waha,'api',lambda method,path,payload,**kw:calls.append((path,payload)) or {'id':str(len(calls))})
    store.enqueue_inbox('semantic-test','message-1','controlled@c.us','Boleh liat rollup bannernya?')
    waha.process(store.claim_inbox('semantic-test'))
    row=store.get_inbox('semantic-test','message-1')
    assert row['status']=='sent'
    assert row['media_selection']['asset_id']=='roll-up-hero'
    assert row['media_selection']['decision']['product_ids']==['roll-up-banner']
    assert [path for path,_ in calls]==['/api/sendImage','/api/sendText']
    assert 'Rp 195.000' in calls[1][1]['text']
    assert store.catalog_context('waha:semantic-test:controlled@c.us')['focus']==['roll-up-banner']


def test_truncated_visual_details_use_complete_controlled_prose(pg_live, monkeypatch):
    from app.backend import product_intent
    seed_active(); catalog.save(record(), 0, 'operator'); store.catalog_feature(True)
    intent=product_intent.ProductIntent(action='show',product_ids=['roll-up-banner'],view='hero',attributes=[],
        exact_visual=False,resolution='resolved',clarification='',changes_product=True)
    monkeypatch.setattr(product_intent,'extract',lambda *a,**kw:intent)
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',lambda **kw:[])
    monkeypatch.setattr(chain,'get_llm',lambda *a:SimpleNamespace(invoke=lambda m:SimpleNamespace(
        content='Harga mulai dari Rp', response_metadata={'finish_reason':'length'})))
    result=chain.RAGChain().run('Lihat roll up','truncated',channel='playground')
    assert result.media_selection['asset_id']=='roll-up-hero'
    assert 'Harga mulai dari Rp' not in result.answer
    assert result.media_decision['answer_validation']=='safe_fallback'


@pytest.mark.parametrize('failure', ['timeout', 'invalid_product'])
def test_failed_semantic_provider_cannot_fall_back_to_keyword_selection(pg_live, monkeypatch, failure):
    from app.backend import product_intent, attachment_answer
    seed_active(); catalog.save(record(),0,'operator'); store.catalog_feature(True)
    def provider(*a, **kw):
        if failure == 'timeout':
            raise TimeoutError('Provider timed out')
        return {'action':'show','product_ids':['invented-product'],'view':'hero','attributes':[],
                'exact_visual':False,'resolution':'resolved','clarification':'','changes_product':True}, {}
    monkeypatch.setattr(product_intent,'structured_response',provider)
    monkeypatch.setattr(product_intent,'extract',real_extract)
    monkeypatch.setattr(vectorstore,'similarity_search_with_score',lambda **kw:[])
    monkeypatch.setattr(chain,'get_llm',lambda *a:SimpleNamespace(invoke=lambda m:SimpleNamespace(content='Foto sudah saya kirim: https://invented.example/photo.png')))
    guarded = []

    def check(text, **kwargs):
        guarded.append(kwargs)
        return False

    monkeypatch.setattr(attachment_answer, 'consistent', check)
    result=chain.RAGChain().run('Kirim foto roll up banner','failed-intent',channel='playground')
    assert len(guarded) == 1 and guarded[0]['selected'] is False
    assert result.media_url is None
    assert result.media_decision['reason']=='intent_failed'
    assert result.media_decision['answer_validation']=='safe_fallback'
    assert 'belum tersedia' not in result.answer
    assert 'invented.example' not in result.answer and 'sudah saya kirim' not in result.answer


def test_structured_provider_transport_has_no_hidden_sdk_retries(monkeypatch):
    from app.backend.models import get_llm
    get_llm.cache_clear()
    model=get_llm('openai/gpt-4.1', structured=True, timeout=20)
    assert model.root_client.max_retries == 0
    assert model.root_client.timeout == 20
    assert model.extra_body == {'provider':{'require_parameters':True}}
    get_llm.cache_clear()
