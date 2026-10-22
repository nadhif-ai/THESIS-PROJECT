"""Idempotent approved-asset import. Run from the repository root with Python 3.12."""

import argparse
import json
from pathlib import Path

from app.admin import catalog, catalog_storage


def import_manifest(path, approved_by):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text())
    existing = {a['asset_id']: a for a in catalog.snapshot()['assets']}
    result = {'imported': [], 'preserved': []}
    for asset in manifest['assets']:
        if not asset['review']['customer_release_approved']:
            raise ValueError('Every imported image must have explicit customer-release approval.')
        identifier = asset['id']
        if identifier in existing:
            result['preserved'].append(identifier)
            continue
        file = (path.parent / asset['file']).resolve()
        if not file.is_relative_to(path.parent / 'images'):
            raise ValueError('Only selected images/ assets may be imported.')
        content = file.read_bytes()
        info = catalog_storage.inspect(content)
        if info['sha256'] != asset['image']['sha256']:
            raise ValueError('Selected image checksum does not match the manifest.')
        info = catalog_storage.publish(identifier, content)
        covered = ['x-banner','y-banner','roll-up-banner'] if asset['product_type']=='standing-banner-comparison' else [asset['product_type']]
        data = {**info, 'asset_id':identifier, 'enabled':True, 'category_id':asset['category_id'],
            'product_type':asset['product_type'], 'covered_product_types':covered, 'role':asset['role'],
            'aliases':catalog.PRODUCTS.get(asset['product_type'],[]), 'description':asset['description_id'],
            'alt_text':asset['alt_text_id'], 'caption':'Ilustrasi produk; model dan finishing dikonfirmasi admin.',
            'depicted_variants':asset['depicted_variants'], 'source_only_variants':asset['source_only_variants'],
            'retrieval_keywords':asset['retrieval_keywords'], 'negative_retrieval_keywords':asset['negative_retrieval_keywords'],
            'is_ai_generated':True, 'provenance':{k:asset[k] for k in ('prompt','input_images','source_sections','manual_review_notes','review')}}
        catalog.save(data, 0, approved_by)
        result['imported'].append(identifier)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', default='dataset/image-product/manifest.json')
    parser.add_argument('--approved-by', required=True)
    options = parser.parse_args()
    print(json.dumps(import_manifest(options.manifest, options.approved_by), indent=2))
