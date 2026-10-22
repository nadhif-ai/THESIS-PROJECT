"""Verify offline catalog assets and refresh their portable metadata exports."""

import csv
import hashlib
import json
from pathlib import Path
import struct
import zlib


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_png(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', f'Invalid PNG signature: {path}'
    offset, compressed, chunks = 8, bytearray(), []
    width = height = depth = color = interlace = None
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        crc = struct.unpack('>I', data[offset + 8 + length:offset + 12 + length])[0]
        assert zlib.crc32(kind + body) & 0xffffffff == crc, f'PNG CRC mismatch: {path}'
        chunks.append(kind)
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            assert compression == filtering == 0
        if kind == b'IDAT':
            compressed.extend(body)
        offset += 12 + length
        if kind == b'IEND':
            break
    assert chunks[0] == b'IHDR' and chunks[-1] == b'IEND'
    assert offset == len(data), f'Trailing or truncated PNG data: {path}'
    pixels = zlib.decompress(compressed)
    assert interlace == 0, 'Verifier expects non-interlaced generated PNGs'
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    stride = (width * channels * depth + 7) // 8
    assert len(pixels) == (stride + 1) * height, f'PNG pixel length mismatch: {path}'
    assert all(pixels[row * (stride + 1)] <= 4 for row in range(height))
    assert width >= 1000 and height >= 1000, f'Unexpected low resolution: {path}'
    return {'width': width, 'height': height, 'format': 'PNG', 'bit_depth': depth,
            'color_type': color, 'bytes': len(data), 'sha256': sha256(path)}


def main():
    manifest_path = ROOT / 'manifest.json'
    m = json.loads(manifest_path.read_text())
    assert len(m['categories']) == 7 and len(m['assets']) == 27
    assert m['runtime_integration_enabled'] is False
    category_ids = {c['id'] for c in m['categories']}
    assert len(category_ids) == 7
    source = ROOT / m['generation']['knowledge_reference']
    lines = source.read_text().splitlines()
    headings = [(i + 1, line[3:]) for i, line in enumerate(lines) if line.startswith('## ')]
    ids, files, hashes = set(), set(), set()
    for asset in m['assets']:
        assert asset['id'] not in ids and asset['file'] not in files
        ids.add(asset['id'])
        files.add(asset['file'])
        assert asset['category_id'] in category_ids
        assert asset['description_id'] and asset['alt_text_id'] and asset['retrieval_keywords']
        assert asset['variants'] and asset['prompt'] and asset['manual_review_notes']
        assert asset['generation_status'] == 'generated'
        assert asset['visual_review_status'] == 'reviewed_representative'
        assert asset['review']['customer_release_approved'] is True
        assert asset['retrieval_enabled'] is False
        assert asset['prices_in_image'] is False
        path = (ROOT / asset['file']).resolve()
        assert path.is_relative_to(ROOT) and path.is_file()
        info = inspect_png(path)
        assert info['sha256'] not in hashes, f'Duplicate image: {path}'
        hashes.add(info['sha256'])
        asset['image'] = info
        refs = []
        for query in asset['source_section_queries']:
            found = next(((j, start, title) for j, (start, title) in enumerate(headings)
                          if title == query or title.startswith(query + ' (')), None)
            assert found, f'Source section missing: {query}'
            j, start, title = found
            end = headings[j + 1][0] - 1 if j + 1 < len(headings) else len(lines)
            refs.append({'file': m['generation']['knowledge_reference'], 'heading': title,
                         'line_start': start, 'line_end': end})
        asset['source_sections'] = refs
        for ref in asset['input_images']:
            assert (ROOT / ref).is_file(), f'Missing input reference: {ref}'
    archived_files = set()
    for draft in m['archived_generations']:
        assert draft['retrieval_enabled'] is False and draft['superseded_by'] in ids
        draft['image'] = inspect_png(ROOT / draft['file'])
        archived_files.add(draft['file'])
    actual = {str(p.relative_to(ROOT)) for p in (ROOT / 'images').glob('*.png')}
    assert actual == files, f'Unmapped or missing selected images: {actual ^ files}'
    actual_drafts = {str(p.relative_to(ROOT)) for p in (ROOT / 'drafts').glob('*.png')}
    assert actual_drafts == archived_files
    m['reference_integrity'] = [dict(file=str(p.relative_to(ROOT)), sha256=sha256(p), bytes=p.stat().st_size)
                                for p in sorted((ROOT / 'references').iterdir()) if p.is_file()]
    m['verification'] = {'date': '2026-10-22', 'selected_images': 27, 'archived_images': len(archived_files),
                         'category_count': 7, 'file_integrity': 'passed', 'mapping': 'passed',
                         'unique_selected_checksums': len(hashes), 'visual_review': 'completed_with_documented_limitations',
                         'admin_product_approval': 'approved_by_user', 'runtime_integration': 'disabled'}
    manifest_path.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n')
    fields = ['id', 'file', 'category', 'role', 'variants', 'description_id', 'retrieval_keywords',
              'width', 'height', 'sha256', 'review_status']
    with (ROOT / 'metadata/catalog.csv').open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        for a in m['assets']:
            row = {key: a.get(key, '') for key in fields}
            row.update(variants=' | '.join(a['variants']), retrieval_keywords=' | '.join(a['retrieval_keywords']),
                       width=a['image']['width'], height=a['image']['height'], sha256=a['image']['sha256'],
                       review_status=a['review']['status'])
            writer.writerow(row)
    with (ROOT / 'metadata/retrieval-documents.jsonl').open('w') as out:
        for a in m['assets']:
            doc = {key: a[key] for key in ('id', 'file', 'category_id', 'category', 'product_type', 'related_asset_ids', 'role', 'variants',
                   'depicted_variants', 'description_id', 'alt_text_id', 'retrieval_keywords',
                   'negative_retrieval_keywords', 'retrieval_text', 'source_sections', 'manual_review_notes',
                   'review', 'retrieval_enabled', 'is_ai_generated', 'is_actual_product_photo')}
            out.write(json.dumps(doc, ensure_ascii=False) + '\n')
    report = ['# Catalog verification', '', '27 selected images across 7 groups; 2 superseded drafts excluded from retrieval exports.', '',
              'PNG signatures, chunk CRCs, decompressed pixel lengths, filter values, dimensions, SHA-256 uniqueness, file mappings, and source references passed.', '',
              'All selected outputs were visually inspected as generated: consistent blue/white branding, neutral studio, no prices or fabricated contacts. Logo resemblance was inspected, not pixel-certified. The user approved all 27 selected illustrations on 2026-10-22; exact physical properties remain unverified.', '',
              'This verifier checks the seed package only. Runtime catalog state and delivery are verified separately.', '',
              '## Manual review by asset', '']
    catalog = ['# Asia Visual Grafika — AI product catalog', '',
               '27 selected photorealistic illustrations. Not photographs of actual shop stock. Prices and specs come from the knowledge source; confirm models/finishing with admin.', '']
    for c in m['categories']:
        items = [a for a in m['assets'] if a['category_id'] == c['id']]
        catalog.extend(['## ' + c['name'], ''])
        for a in items:
            report.extend(['### ' + a['id'], '', *('- ' + note for note in a['manual_review_notes']), ''])
            catalog.extend(['### ' + a['id'], '', f"![{a['alt_text_id']}]({a['file']})", '',
                            a['description_id'], '', 'Role: ' + a['role'] + '. Admin product approval: approved by user.', ''])
    (ROOT / 'VERIFICATION.md').write_text('\n'.join(report).rstrip() + '\n')
    (ROOT / 'CATALOG.md').write_text('\n'.join(catalog).rstrip() + '\n')
    (ROOT / 'metadata/verification.json').write_text(json.dumps(m['verification'], indent=2) + '\n')
    print(json.dumps(m['verification'], indent=2))


if __name__ == '__main__':
    main()
