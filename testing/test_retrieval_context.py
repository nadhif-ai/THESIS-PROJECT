from langchain_core.documents import Document

from app.backend.retrieval_context import expand_sections
from pathlib import Path
import json


def record(index, text, section='Kertas', **metadata):
    return {'id': str(index), 'document': text, 'metadata': {
        'source': 'bahan.txt', 'document_id': 'snapshot-blob',
        'section_2': section, 'chunk_index': index, **metadata}}


def test_comparison_recovers_the_whole_section_and_price_without_fake_cosines():
    records = [record(i, f'Kertas {i}: karakteristik lengkap.') for i in range(7)]
    records += [record(7, 'Linen 1S: 11–50 lembar Rp 5.000.', 'Harga')]
    records += [record(8, 'Kertas dari bagian lain.', 'Stiker')]
    selected = [(Document(page_content=records[i]['document'],
                          metadata={**records[i]['metadata'], 'chunk_id': str(i)}), .2)
                for i in (5, 7)]
    result = expand_sections('Apa bedanya tujuh kertas dan harganya?', selected, records)
    assert {doc.metadata['chunk_index'] for doc, _ in result} == set(range(8))
    assert next(distance for doc, distance in result if doc.metadata['chunk_id'] == '5') == .2
    assert all(distance is None for doc, distance in result
               if doc.metadata.get('retrieval_method') == 'section_expansion')


def test_expansion_respects_filter_page_budget_and_removes_identical_text():
    records = [record(0, 'Linen: bahan sertifikat', page=1),
               record(1, 'Tarif 20 lembar: Rp 100.000', page=1),
               record(2, 'Linen: bahan sertifikat', page=1),
               record(3, 'Private unrelated page', page=2),
               record(4, 'Wrong intent', page=1, intent_type='other')]
    selected = [(Document(page_content=records[0]['document'], metadata={
        **records[0]['metadata'], 'chunk_id': '0'}), .1)]
    result = expand_sections('Bandingkan bahan', selected, records,
                             filter_dict={'page': 1}, budget=100)
    assert [doc.page_content for doc, _ in result] == [records[0]['document'], records[1]['document'], records[4]['document']]
    assert sum(len(doc.page_content) for doc, _ in result) <= 100


def test_single_fact_only_expands_immediate_neighbors():
    records = [record(i, str(i)) for i in range(7)]
    selected = [(Document(page_content='3', metadata={**records[3]['metadata'], 'chunk_id': '3'}), .1)]
    assert {doc.page_content for doc, _ in expand_sections('Bahan Linen?', selected, records)} == {'2', '3', '4'}


def test_recorded_playground_selection_recovers_all_paper_details_and_linen_tier():
    from app.admin.global_knowledge import documents

    root = Path(__file__).resolve().parents[1]
    evidence = json.loads((root / 'docs/playground-trace-evidence.json').read_text())['retrieval']
    selected = [(Document(page_content=row['text'], metadata={
        'source': row['source'], 'chunk_index': row['chunk_index'], 'chunk_id': row['chunk_id'],
        'document_id': '', 'section_1': row['text'].split(' > ')[0],
        'section_2': row['text'].split(' > ')[1].split('\n')[0],
        **({'section_3': row['text'].split(' > ')[2].split('\n')[0]} if len(row['text'].split(' > ')) > 2 else {}),
    }), .2) for row in evidence['selected']]
    records = []
    for name in ('02_spesifikasi_bahan_dan_finishing.txt', '04_daftar_estimasi_harga.txt'):
        source = {'name': name, 'format': 'txt', 'pages': [{'text': (root / 'dataset/knowledge_base' / name).read_text()}]}
        for doc in documents(source, {'chunk_size': 1000, 'chunk_overlap': 100}):
            records.append({'id': f'{name}:{doc.metadata["chunk_index"]}', 'document': doc.page_content,
                            'metadata': doc.metadata})
    # Local source headings have changed since the recorded production snapshot.
    for doc, _ in selected:
        matching = next(r['metadata'] for r in records if
            r['metadata']['source'] == doc.metadata['source'] and
            r['metadata'].get('section_2') == doc.metadata.get('section_2') and
            r['metadata'].get('section_3') == doc.metadata.get('section_3'))
        doc.metadata['section_1'] = matching['section_1']
    result = expand_sections(evidence['query'], selected, records)
    context = '\n'.join(doc.page_content for doc, _ in result)
    for material in ('HVS', 'Art Paper', 'Art Carton', 'BW / Blues White', 'Linen', 'Concorde', 'Photopaper'):
        assert material in context
    assert 'Kertas khusus cetak foto' in context
    assert 'Pesan 11 hingga 50 lembar: Rp 5.000' in context
    assert sum(len(doc.page_content) for doc, _ in result) <= 18000
