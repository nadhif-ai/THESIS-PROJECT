from langchain_core.documents import Document
from app.backend.retrieval_ranking import rank_candidates


def test_lexical_evidence_can_recover_a_lower_ranked_policy_without_fake_cosines():
    candidates = [(Document(page_content="Panduan berkas dan resolusi gambar", metadata={"chunk_id": "file"}), 0.1),
                  (Document(page_content="Harga brosur untuk pelanggan", metadata={"chunk_id": "price"}), 0.2),
                  (Document(page_content="Klaim salah cetak: kesalahan operator toko mendapat cetak ulang", metadata={"chunk_id": "policy"}), 0.3)]
    ranked = rank_candidates("klaim salah cetak dari toko", candidates, 2)
    assert ranked[0][0].metadata["chunk_id"] == "policy"
    assert ranked[0][1] == 0.3
    assert "retrieval_recipe" not in candidates[2][0].metadata


def test_no_lexical_matches_preserves_cosine_order_and_duplicate_chunks_are_removed():
    first = Document(page_content="First passage", metadata={"chunk_id": "same"})
    second = Document(page_content="Second passage", metadata={"chunk_id": "other"})
    ranked = rank_candidates("unmatched", [(first, 0.1), (first, 0.2), (second, 0.3)], 3)
    assert [(doc.metadata["chunk_id"], distance) for doc, distance in ranked] == [("same", 0.1), ("other", 0.3)]


def test_repeated_source_text_with_different_ids_does_not_consume_candidate_slots():
    candidates = [(Document(page_content=text, metadata={'source': 'harga.txt', 'chunk_id': str(i)}), .1)
                  for i, text in enumerate(('Linen Rp 5.000', 'Linen  Rp 5.000', 'Concord Rp 5.000'))]
    assert len(rank_candidates('harga', candidates, 3)) == 2


def test_reranking_uses_provider_indices_and_keeps_cosine_evidence(monkeypatch):
    from types import SimpleNamespace
    from app.backend import retrieval_ranking as ranking
    sent = []
    def post(url, **kwargs):
        sent.append(kwargs)
        return SimpleNamespace(status_code=200, json=lambda: {"data": [{"index": 1, "score": .9}, {"index": 0, "score": .1}]})
    monkeypatch.setattr(ranking.requests, 'post', post)
    candidates = [(Document(page_content='Kontak admin', metadata={'chunk_id': 'contact'}), .1),
                  (Document(page_content='Alamat fisik toko', metadata={'chunk_id': 'address'}), .3)]
    result = ranking.rerank_candidates('Alamat toko?', candidates, 1)
    assert result[0][0].metadata['chunk_id'] == 'address'
    assert result[0][1] == .3
    assert result[0][0].metadata['rerank_score'] == .9
    assert 'rerank_score' not in candidates[1][0].metadata
    assert sent[0]['timeout'] == (3, 8)
    assert sent[0]['json']['documents'][1]['text'] == 'Alamat fisik toko'


def test_reranker_failure_or_invalid_indices_falls_back_without_losing_evidence(monkeypatch):
    from types import SimpleNamespace
    from app.backend import retrieval_ranking as ranking
    candidates = [(Document(page_content='First', metadata={'chunk_id': 'first'}), .1),
                  (Document(page_content='Second', metadata={'chunk_id': 'second'}), .2)]
    for response in [SimpleNamespace(status_code=429), SimpleNamespace(status_code=200,
            json=lambda: {'data': [{'index': 0, 'score': .9}, {'index': 0, 'score': .2}]}),
            SimpleNamespace(status_code=200, json=lambda: {'data': ['bad', 'rows']})]:
        monkeypatch.setattr(ranking.requests, 'post', lambda *a, **k: response)
        result = ranking.rerank_candidates('query', candidates, 2)
        assert [doc.metadata['chunk_id'] for doc, _ in result] == ['first', 'second']
        assert all(doc.metadata['rerank_fallback'] for doc, _ in result)
        assert 'rerank_fallback' not in candidates[0][0].metadata
