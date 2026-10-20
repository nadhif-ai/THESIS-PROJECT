"""No external providers: exercise shortcuts and error tracing on read-only deployments."""

from types import SimpleNamespace

import pytest

from app.backend import chain


@pytest.mark.parametrize("question,source", [("hi", "Greeting"), ("2", "Menu")])
def test_shortcuts_need_no_settings_queries_or_writable_version_files(monkeypatch, tmp_path, question, source):
    root = tmp_path / "knowledge_base"
    root.mkdir()
    (root / "05_daftar_pertanyaan_populer.txt").write_text("[KATEGORI_2]\nFormat file cetak apa?\n[KATEGORI_3]\nJam buka?\n")
    rag = chain.RAGChain.__new__(chain.RAGChain)
    rag.settings = SimpleNamespace(structured_kb_dir=str(tmp_path), vector_store="pinecone")
    monkeypatch.setattr(chain.store, "prompt_turns", lambda *args: [])
    monkeypatch.setattr(chain.store, "record_conversation", lambda *args, **kwargs: None)
    monkeypatch.setattr(chain.store, "version_info", lambda **kwargs: {"manifest": {}, "namespace": "synthetic"})
    monkeypatch.setattr(chain.store, "get_setting", lambda *args: pytest.fail("Shortcut performed a database query"))
    response = rag.run(question, "synthetic", langsmith_extra={"enabled": False})
    assert response.answer_source == source
    if source == "Menu":
        assert "Format file cetak apa?" in response.answer
        assert "Jam buka?" not in response.answer


def test_trace_formatter_preserves_original_generation_exception():
    assert chain._trace_outputs(None) == {}
