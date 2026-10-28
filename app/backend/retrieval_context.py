"""Complete selected sections using records from the pinned knowledge snapshot."""

import re

from langchain_core.documents import Document
from langsmith import traceable


def _section(metadata):
    headings = tuple(metadata.get(key) for key in ('section_1', 'section_2', 'section_3'))
    if not any(headings):
        return None
    return (metadata.get('source'), metadata.get('document_id'), metadata.get('page'), *headings)


@traceable(name='knowledge-context-expansion', run_type='retriever')
def expand_sections(query, selected, records, *, filter_dict=None, budget=18000):
    broad = bool(re.search(r'banding|perbedaan|beda|pilihan|ketujuh|tujuh|semua|jenis|harga|biaya|tarif', query, re.I))
    # shortcut: expand two sections within the context budget; add targeted subqueries if coverage replays still miss facts.
    sections = list(dict.fromkeys(_section(doc.metadata) for doc, _ in selected
                                 if _section(doc.metadata)))[:2]
    result, seen, used = [], set(), 0

    def append(doc, distance):
        nonlocal used
        identity = (doc.metadata.get('source'), ' '.join(doc.page_content.split()))
        if identity in seen or used + len(doc.page_content) > budget:
            return
        seen.add(identity)
        used += len(doc.page_content)
        result.append((doc, distance))

    for doc, distance in selected:
        append(doc, distance)
    for section in sections:
        anchors = [doc.metadata.get('chunk_index') for doc, _ in selected
                   if _section(doc.metadata) == section]
        for record in sorted(records, key=lambda record: record['metadata'].get('chunk_index', 0)):
            metadata = record['metadata']
            if _section(metadata) != section or any(metadata.get(k) != v for k, v in (filter_dict or {}).items()):
                continue
            if not broad and not any(isinstance(index, (int, float)) and
                    abs(metadata.get('chunk_index', -100) - index) <= 1 for index in anchors):
                continue
            append(Document(page_content=record['document'], metadata={
                **metadata, 'chunk_id': record['id'], 'retrieval_method': 'section_expansion',
            }), None)
    # Restore document order within a section so a heading precedes its continued details.
    order = list(dict.fromkeys(_section(doc.metadata) for doc, _ in result))
    return sorted(result, key=lambda pair: (order.index(_section(pair[0].metadata)),
                                           pair[0].metadata.get('chunk_index', 0)))
