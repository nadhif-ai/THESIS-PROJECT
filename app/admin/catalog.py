"""Editable catalog records; illustrative metadata never enters answer context."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.admin import store

CATEGORIES = {
    'banner-spanduk': 'Banner & Spanduk',
    'stiker-meteran': 'Stiker Meteran',
    'standing-banner': 'X/Y/Roll Up Banner',
    'stiker-a3-kiss-cut': 'Stiker A3+ / Kiss Cut',
    'digital-print-a3': 'Digital Print A3+',
    'id-card-kartu-nama': 'ID Card & Kartu Nama',
    'other-physical-printing': 'Other Physical Printing Products',
}
PRODUCTS = {
    'banner-spanduk': ['banner', 'spanduk', 'flexi'],
    'stiker-meteran': ['stiker meteran', 'sticker meteran', 'one way vision', 'owv', 'vinyl ritrama'],
    'x-banner': ['x banner', 'xbanner', 'banner x'],
    'y-banner': ['y banner', 'ybanner', 'banner y'],
    'roll-up-banner': ['roll up banner', 'rollup banner', 'roll up', 'rollup', 'roll banner'],
    'stiker-a3-kiss-cut': ['stiker a3', 'sticker a3', 'kiss cut', 'kisscut'],
    'digital-print-a3': ['digital print', 'cetak a3', 'print a3'],
    'id-card': ['id card', 'idcard', 'kartu id'],
    'kartu-nama': ['kartu nama', 'business card'],
    'brosur-flyer': ['brosur', 'flyer'], 'nota-ncr': ['nota', 'ncr'],
    'stempel': ['stempel'], 'poster-albatros': ['poster'],
    'kalender-meja': ['kalender'], 'e-money-custom-uv': ['e money', 'emoney'],
    'plakat-akrilik': ['plakat'], 'yasin-buku-saku': ['yasin'],
    'tumbler-custom': ['tumbler'], 'pin-aksesoris': ['pin'],
    'lanyard': ['lanyard'], 'korek-api-custom': ['korek api'],
}
PRODUCT_CATEGORIES = {p: ('standing-banner' if p in ('x-banner','y-banner','roll-up-banner')
    else 'id-card-kartu-nama' if p in ('id-card','kartu-nama')
    else p if p in CATEGORIES else 'other-physical-printing') for p in PRODUCTS}


class Conflict(ValueError):
    pass


class AssetEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    asset_id: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{2,99}$')
    category_id: str = Field(max_length=60)
    product_type: str = Field(max_length=80)
    covered_product_types: list[str] = Field(min_length=1, max_length=20)
    role: Literal['hero', 'material_comparison', 'form_comparison', 'finishing_comparison', 'finishing_detail']
    aliases: list[str] = Field(default_factory=list, max_length=40)
    description: str = Field(min_length=1, max_length=2500)
    alt_text: str = Field(min_length=1, max_length=400)
    caption: str = Field(min_length=1, max_length=240)
    depicted_variants: list[str] = Field(default_factory=list, max_length=40)
    visual_attributes: dict[Literal['size', 'material', 'finish', 'type', 'shape'], list[str]] = Field(default_factory=dict)
    source_only_variants: list[str] = Field(default_factory=list, max_length=40)
    retrieval_keywords: list[str] = Field(default_factory=list, max_length=60)
    negative_retrieval_keywords: list[str] = Field(default_factory=list, max_length=60)
    enabled: bool = Field(strict=True, default=True)


def validate(data):
    fields = AssetEdit.model_validate({k: v for k, v in data.items() if k in AssetEdit.model_fields}).model_dump()
    if fields['category_id'] not in CATEGORIES:
        raise ValueError('Choose one of the seven catalog groups.')
    if not set(fields['covered_product_types']) <= PRODUCTS.keys():
        raise ValueError('Choose recognized catalog products.')
    if any(PRODUCT_CATEGORIES[p] != fields['category_id'] for p in fields['covered_product_types']):
        raise ValueError('The depicted products must belong to the selected group.')
    if fields['product_type'] not in PRODUCTS and fields['role'] != 'form_comparison':
        raise ValueError('Choose a recognized product.')
    for key, value in fields.items():
        if isinstance(value, list) and any(not x.strip() or len(x) > 240 for x in value):
            raise ValueError('Catalog terms must contain 1–240 characters.')
    for values in fields['visual_attributes'].values():
        if len(values) > 20 or any(not v.strip() or len(v) > 100 for v in values):
            raise ValueError('Verified visual attributes require up to 20 nonempty values of at most 100 characters.')
    fields['visual_attributes'] = {key: list(dict.fromkeys(v.strip().casefold() for v in values))
                                   for key, values in fields['visual_attributes'].items()}
    if re.search(r'\b(rp\.?|idr)\s*\d', fields['caption'], re.IGNORECASE):
        raise ValueError('Keep prices in the knowledge base, not image captions.')
    sha = data.get('sha256', '')
    mime = data.get('mime_type')
    extension = 'png' if mime == 'image/png' else 'jpg'
    expected_key = f"{fields['asset_id']}/{sha}.{extension}"
    if (not re.fullmatch('[a-f0-9]{64}', sha) or mime not in ('image/png', 'image/jpeg')
            or data.get('object_key') != expected_key):
        raise ValueError('The catalog image must be a verified catalog object.')
    return {**data, **fields}


def snapshot():
    data = store.catalog_snapshot()
    return {**data, 'categories': CATEGORIES, 'products': PRODUCTS}


def save(data, expected_revision, approved_by):
    return store.save_catalog_asset(validate(data), expected_revision, approved_by)


def set_enabled(asset_id, enabled, expected_revision, approved_by):
    asset = next((a for a in snapshot()['assets'] if a['asset_id'] == asset_id), None)
    if not asset:
        raise ValueError('Catalog image was not found.')
    return save({**asset, 'enabled': enabled}, expected_revision, approved_by)


def asset_enabled(asset_id):
    return store.catalog_asset_enabled(asset_id)
