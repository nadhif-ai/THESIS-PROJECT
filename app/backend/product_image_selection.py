"""Select approved illustrations from validated intent, without interpreting customer text."""

from app.backend.product_intent import ProductIntent


def select(intent: ProductIntent, assets, *, focus=()):
    resolved = intent.resolution == 'resolved'
    targets = intent.product_ids if resolved and intent.product_ids else list(focus)
    result = {'asset': None, 'focus': targets, 'explicit': resolved and intent.action != 'none',
              'reason': 'image_not_requested', 'product_ids': intent.product_ids,
              'intent_resolution': intent.resolution, 'illustrative': False}
    if not resolved:
        return {**result, 'reason': 'intent_' + intent.resolution}
    if intent.action == 'none':
        return result
    if len(targets) > 1 and intent.view != 'comparison':
        return {**result, 'reason': 'clarify_multiple_products'}
    candidates = []
    for asset in assets:
        if not asset.get('enabled') or not set(targets) <= set(asset['covered_product_types']):
            continue
        role = asset['role']
        if intent.view == 'comparison':
            if not role.endswith('comparison'):
                continue
        elif role != intent.view:
            continue
        comparison_attributes = [a for a in intent.attributes if a.name != 'size'] if intent.view == 'comparison' else []
        constraints = intent.attributes if intent.exact_visual else comparison_attributes
        if intent.exact_visual or constraints:
            # Only explicitly curated attributes can substantiate exact visual claims.
            verified = asset.get('visual_attributes', {})
            if not constraints or any(a.value.casefold() not in
                    [v.casefold() for v in verified.get(a.name, [])] for a in constraints):
                continue
        candidates.append(asset)
    if not candidates:
        if len(targets) > 1:
            return {**result, 'reason': 'clarify_multiple_products'}
        return {**result, 'reason': 'exact_visual_unavailable' if intent.exact_visual else 'no_matching_asset'}
    selected = min(candidates, key=lambda a: (len(a['covered_product_types']), a['asset_id']))
    return {**result, 'asset': selected, 'reason': 'explicit_comparison' if intent.action == 'compare' else 'explicit_example',
            'illustrative': not intent.exact_visual}
