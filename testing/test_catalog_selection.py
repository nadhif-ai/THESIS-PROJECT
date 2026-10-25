import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.backend.product_intent import ProductIntent, failed_intent
from app.backend.product_image_selection import select
from testing.test_product_catalog import record


def intent(action='show', products=('roll-up-banner',), **overrides):
    return ProductIntent(action=action, product_ids=list(products), view=overrides.pop('view', 'hero'),
        attributes=overrides.pop('attributes', []), exact_visual=overrides.pop('exact_visual', False),
        resolution=overrides.pop('resolution', 'resolved'), clarification='', changes_product=True, **overrides)


def test_nonvisual_and_failed_intents_never_attach_or_guess_identity():
    assert select(intent('none'), [record()])['asset'] is None
    decision = select(failed_intent(), [record()], focus=['x-banner'])
    assert decision['asset'] is None and decision['focus'] == ['x-banner']
    assert select(intent(resolution='ambiguous'), [record()], focus=['x-banner'])['focus'] == ['x-banner']


def test_catalog_identity_is_independent_of_factual_evidence_and_repeat_history():
    for action in ('show', 'repeat'):
        decision = select(intent(action), [record()], focus=['x-banner'])
        assert decision['asset']['asset_id'] == 'roll-up-hero'
        assert decision['focus'] == ['roll-up-banner']
    assert select(intent(), [{**record(), 'enabled': False}])['asset'] is None


def test_size_order_uses_hero_but_exact_visual_requires_verified_attributes():
    size = [{'name': 'size', 'value': '60 x 160 cm', 'evidence': '60 x 160 cm'}]
    assert select(intent(attributes=size), [record()])['asset']
    assert select(intent(attributes=size, exact_visual=True), [record()])['reason'] == 'exact_visual_unavailable'
    asset = {**record(), 'visual_attributes': {'size': ['60 x 160 cm']}}
    assert select(intent(attributes=size, exact_visual=True), [asset])['asset']


def test_multiple_products_require_a_comparison_not_incidental_fallback():
    comparison = {**record(), 'asset_id': 'comparison', 'role': 'form_comparison',
                  'covered_product_types': ['x-banner', 'roll-up-banner']}
    assert select(intent(), [comparison])['asset'] is None
    assert select(intent(products=['x-banner', 'roll-up-banner']), [comparison])['reason'] == 'clarify_multiple_products'
    assert select(intent('compare', products=['x-banner', 'roll-up-banner'], view='comparison'), [record(), comparison])['asset'] == comparison


def test_approved_catalog_has_correct_hero_for_every_product_and_explicit_comparison_roles():
    manifest = json.loads(Path('dataset/image-product/manifest.json').read_text())
    assets = [{**a, 'asset_id': a['id'], 'enabled': True,
        'covered_product_types': ['x-banner','y-banner','roll-up-banner'] if a['product_type']=='standing-banner-comparison' else [a['product_type']]}
        for a in manifest['assets']]
    for asset in assets:
        is_comparison = asset['role'].endswith('comparison')
        request = intent('compare' if is_comparison else 'show', products=asset['covered_product_types'],
                         view='comparison' if is_comparison else asset['role'])
        assert select(request, assets)['asset']['asset_id'] == asset['asset_id']


def test_unknown_product_and_extra_output_fields_rejected():
    with pytest.raises(ValidationError):
        intent(products=['invented-product'])
    with pytest.raises(ValidationError):
        intent(url='https://invented.example/image.png')
    with pytest.raises(ValidationError):
        intent(products=[])


def test_comparison_cannot_substitute_unshown_materials():
    comparison = {**record(), 'role':'material_comparison',
                  'visual_attributes':{'material':['china','korea']}}
    requested = intent('compare', view='comparison', attributes=[
        {'name':'material','value':'satin','evidence':'satin'}])
    assert select(requested, [comparison])['asset'] is None


def test_explicit_repeat_can_reuse_comparison_view():
    comparison = {**record(), 'role':'form_comparison', 'covered_product_types':['x-banner','roll-up-banner']}
    repeat = intent('repeat', products=['x-banner','roll-up-banner'], view='comparison')
    assert select(repeat, [comparison])['asset'] == comparison


def test_unavailable_multi_product_comparison_requests_a_choice():
    request = intent('compare', products=['roll-up-banner','plakat-akrilik'], view='comparison')
    assert select(request, [record()])['reason'] == 'clarify_multiple_products'
