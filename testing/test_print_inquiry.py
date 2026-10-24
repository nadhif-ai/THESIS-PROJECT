"""Conversation routing regressions without paid model or embedding calls."""

from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from app.admin import catalog, store
from app.backend import chain, vectorstore


@pytest.fixture
def conversation(monkeypatch):
    turns, prompts, searches = [], [], []
    monkeypatch.setattr(catalog, "snapshot", lambda: {"enabled": False, "assets": [], "revision": 0})
    monkeypatch.setattr(store, "prompt_turns", lambda *args: list(turns))
    monkeypatch.setattr(store, "record_conversation", lambda session, channel, question, answer, *args, **kwargs: turns.append((question, answer)))
    monkeypatch.setattr(chain, "clear_session_history", lambda session: turns.clear())
    monkeypatch.setattr(store, "get_setting", lambda key, default=None: default)

    def invoke(messages):
        prompts.append(messages)
        return SimpleNamespace(content="Ringkasan kebutuhan cetak. Cabang mana yang Kakak pilih?")

    def search(**kwargs):
        searches.append(kwargs["query"])
        return [(Document(page_content="Informasi cabang dari knowledge aktif.", metadata={"source": "sop.txt"}), 0.1)]

    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace(invoke=invoke))
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", search)
    rag = chain.RAGChain.__new__(chain.RAGChain)
    rag.settings = SimpleNamespace(vector_store="offline", semantic_top_k=4, openrouter_model="offline", product_intent_model="offline")
    return SimpleNamespace(rag=rag, turns=turns, prompts=prompts, searches=searches)


def test_first_greeting_or_reset_explains_capabilities_but_returning_greeting_is_short(conversation):
    rag = conversation.rag
    first = rag.run("hey", "customer", channel="whatsapp")
    assert "Sahabat Asia" in first.answer
    assert "1." in first.answer and "4." in first.answer
    assert "reset" in first.answer and "menu" in first.answer
    again = rag.run("halo", "customer", channel="whatsapp")
    assert "1." not in again.answer
    reset = rag.run("reset", "customer", channel="whatsapp")
    assert "1." in reset.answer and "Sahabat Asia" in reset.answer
    assert len(conversation.turns) == 1
    assert not conversation.prompts


def test_approval_preserves_specifications_and_retrieves_next_step_information(conversation):
    conversation.turns.append(("Stiker vinyl 10 x 10 cm 50 pcs", "Harga perlu konfirmasi admin. Mau saya rangkum untuk dilanjutkan ke cabang?"))
    result = conversation.rag.run("oke", "customer", channel="whatsapp")
    assert result.answer_source == "naive_rag"
    assert conversation.prompts[0][-3].content == "Stiker vinyl 10 x 10 cm 50 pcs"
    assert "alamat" in conversation.searches[0] and "admin" in conversation.searches[0]


def test_resolved_product_keeps_customer_dimensions_and_quantity_in_retrieval(conversation, monkeypatch):
    from app.backend import product_intent

    intent = product_intent.ProductIntent(action='none', product_ids=['stiker-a3-kiss-cut'],
        view='hero', attributes=[], exact_visual=False, resolution='resolved',
        clarification='', changes_product=False)
    monkeypatch.setattr(product_intent, 'extract', lambda *args, **kwargs: intent)
    conversation.turns.append(("Stiker 5 x 5 cm sebanyak 100 pcs", "Bahannya mau cromo atau vinyl?"))
    conversation.rag.run("Vinyl saja", "customer", channel="whatsapp")
    query = conversation.searches[0]
    assert "Vinyl saja" in query and "stiker a3" in query
    assert "5 x 5 cm" in query and "100 pcs" in query


def test_numeric_branch_answer_does_not_open_category_menu(conversation):
    conversation.turns.append(("Mau pesan stiker", "Pilih cabang: 1. Cabang A atau 2. Cabang B?"))
    result = conversation.rag.run("2", "customer")
    assert result.answer_source == "naive_rag"
    assert conversation.prompts[0][-2].content.startswith("Pilih cabang")


def test_explicit_menu_still_accepts_category_numbers(conversation, tmp_path):
    conversation.rag.settings.structured_kb_dir = str(tmp_path)
    folder = tmp_path / "knowledge_base"
    folder.mkdir()
    (folder / "05_daftar_pertanyaan_populer.txt").write_text("[KATEGORI_2]\nFormat file apa?\n")
    conversation.rag.run("menu", "customer")
    result = conversation.rag.run("2", "customer")
    assert result.answer_source == "Menu" and "Format file apa?" in result.answer
    assert not conversation.prompts


def test_explicit_evaluation_history_overrides_saved_session(conversation):
    conversation.turns.append(("Hi", chain._WELCOME_GREETING_TEXT))
    conversation.rag.run("halo", "evaluation", history_turns=[])
    assert "Sahabat Asia" in conversation.turns[-1][1]


def test_saved_custom_style_cannot_remove_inquiry_boundaries(conversation):
    from app.backend.prompt_template import prompt_snapshot

    snapshot = prompt_snapshot("Untuk oke, cukup respons ringan tanpa mengulang seluruh pesanan.")
    conversation.turns.append(("Mau pesan stiker", "Saya bantu rangkum."))
    conversation.rag.run("approve", "customer", prompt_config=snapshot)
    system = conversation.prompts[0][0].content
    assert "RINGKASAN KEBUTUHAN CETAK" in system
    assert "belum masuk antrean cetak" in system
    assert "cabang terdekat" in system


def test_cancel_order_request_does_not_reset_conversation(conversation):
    conversation.turns.append(("Pesanan kemarin mau diubah", "Hubungi admin untuk pengecekan."))
    result = conversation.rag.run("batal", "customer")
    assert result.answer_source == "naive_rag"
    assert conversation.prompts[0][-3].content == "Pesanan kemarin mau diubah"


def test_greetings_persist_per_channel_and_reset_preserves_audit(pg_live, monkeypatch):
    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace())
    rag = chain.RAGChain()
    first = rag.run("halo", "same-id", channel="whatsapp")
    assert "Sahabat Asia" in first.answer
    assert "Sahabat Asia" not in rag.run("halo", "same-id", channel="whatsapp").answer
    assert "Sahabat Asia" in rag.run("halo", "same-id", channel="playground").answer
    rag.run("reset", "same-id", channel="whatsapp")
    assert len(store.conversations()) == 4
    assert len(store.prompt_turns("same-id", "whatsapp")) == 1
