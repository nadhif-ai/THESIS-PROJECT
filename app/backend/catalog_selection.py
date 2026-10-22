"""Bounded, deterministic product image decisions shared by all preview/delivery paths."""

import re

from app.admin.catalog import PRODUCTS


def normalized(text):
    text = text.lower().replace('×', 'x')
    text = re.sub(r'(?<=\d)x(?=\d)', ' x ', text)
    text = re.sub(r'(?<=\d)(?=(?:cm|mm|gsm|ml)\b)', ' ', text)
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def contains(text, term):
    return bool(re.search(r'(?<!\w)' + re.escape(normalized(term)) + r'(?!\w)', text))


def products(text, assets=()):
    text = normalized(text)
    aliases = {k: list(v) for k, v in PRODUCTS.items()}
    for a in assets:
        if a['product_type'] in aliases:
            aliases[a['product_type']] += a.get('aliases', [])
    found = {p for p, terms in aliases.items() if any(contains(text, t) for t in terms)}
    if found & {'x-banner','y-banner','roll-up-banner','poster-albatros'}:
        # The generic word "banner" inside a stand name is not a second product.
        without_stands = text
        for p in ('x-banner','y-banner','roll-up-banner'):
            for term in sorted(aliases[p], key=len, reverse=True):
                without_stands = re.sub(r'(?<!\w)' + re.escape(normalized(term)) + r'(?!\w)', '', without_stands)
        if not any(contains(without_stands, t) for t in aliases['banner-spanduk']):
            found.discard('banner-spanduk')
    return sorted(found)


_VARIANTS = {
    'china': ['china'], 'korea': ['korea'], 'albatros': ['albatros'],
    'transparan': ['transparan','transparent'], 'owv': ['owv','one way vision'],
    'ritrama': ['ritrama'], 'art paper': ['art paper'], 'art carton': ['art carton','art karton'],
    'hvs': ['hvs'], 'bc': ['bc'], 'linen': ['linen'], 'concorde': ['concorde'],
    'photo paper': ['photo paper','kertas foto'], 'glossy': ['glossy','gloss'], 'doff': ['doff','matte'],
    'niagara': ['niagara'], 'sakura': ['sakura'], 'smart led': ['smart led'],
}

_VARIANT_STOP = set('tanpa dengan dan atau with without laminasi ukuran paket custom cetak print kartu id card banner stiker sticker a3 paper gsm cm mm meter lembar buku per bentuk sederhana x y'.split())


def variant_terms(assets, targets):
    terms = set()
    for asset in assets:
        if not set(targets) <= set(asset['covered_product_types']):
            continue
        for variant in asset.get('source_only_variants', []) + asset.get('depicted_variants', []):
            if 'not visually authenticated' in variant:
                continue
            value = normalized(variant)
            for product in targets:
                for alias in sorted(PRODUCTS[product], key=len, reverse=True):
                    value = re.sub(r'(?<!\w)' + re.escape(normalized(alias)) + r'(?!\w)', '', value)
            terms.update(word for word in value.split() if word not in _VARIANT_STOP and word.isalnum() and not word.isdigit())
    return terms


def image_request(question, *, product_context=False):
    text = normalized(question)
    visual = r'(?:gambar(?:nya)?|foto(?:nya)?|preview|visual(?:nya)?)'
    view = r'(?:lihat|liat|tunjukkan|tunjukin)'
    negation = r'(?:jangan|tidak usah|tidak perlu|tak usah|ga usah|gak usah|nggak usah|gausah)'
    visual_action = rf'(?:{visual}|contoh(?:nya)?|{view}|kirim(?:kan|in)?)'
    if re.search(r'\b(?:teks|text)\s*(?:saja|aja|only)\b|\btext only\b', text):
        return False
    if re.search(rf'\b{negation}\b(?:\s+\w+){{0,3}}\s+{visual_action}\b|\b{visual}(?:\s+\w+){{0,4}}\s+{negation}\b|\btanpa\s+{visual}\b', text):
        return False
    # Photo-printing terms describe the order rather than an attachment request.
    request_text = re.sub(r'\b(?:cetak|print|kertas|untuk)\s+foto\b', '', text)
    artwork_question = re.search(r'\b(?:file|format|resolusi|dpi|pixel|piksel)\b', text)
    visual_command = re.search(rf'\b(?:kirim(?:kan|in)?|tampilkan|tunjukkan|tunjukin|{view})\b', text)
    if artwork_question and not visual_command:
        return False
    if re.search(r'\b' + visual + r'\b', request_text):
        return True
    if re.search(r'\bcontoh(?:nya)?\b', text) and not re.search(r'\bcontoh(?:nya)?\s+(?:harga|ukuran|bahan|spesifikasi|hitung\w*|perhitungan|kalkulasi|total|estimasi)\b', text):
        return True
    if re.search(rf'\b{view}\s+(?:daftar\s+)?(?:harga|tarif|ongkir|ukuran|bahan|spesifikasi)\b', text):
        return False
    return bool(product_context and re.search(
        r'\b(?:mau|boleh|bisa|ingin|pengen)\s+(?:lihat|liat)|\b(?:lihat|liat|tunjukkan|tunjukin)\b|\bkirim(?:kan|in)?\s+(?:itu\s+)?(?:lagi|ulang)\b', text))


def select(question, assets, evidence, *, focus=(), seen=()):
    text = normalized(question)
    direct = products(question, assets)
    explicit = image_request(question, product_context=bool(direct or focus))
    comparison = bool(re.search(r'\b(beda\w*|banding\w*|versus|vs|pilihan bahan|macam bahan|jenis bahan)\b', text))
    detail = bool(re.search(r'\b(detail|hasil potong|potongan)\b', text)) or (explicit and contains(text, 'kiss cut'))
    ambiguous = (not direct and bool(re.search(r'\b(stiker|sticker|banner|kartu)\b', text)))
    targets = direct or ([] if ambiguous else list(focus))
    result = {'asset': None, 'reason': '', 'focus': targets, 'explicit': explicit}

    def skip(reason):
        return {**result, 'reason': reason}

    non_product = re.search(r'\b(software|aplikasi|tutorial|jam buka|alamat toko|kontak admin)\b', text)
    shipping = not explicit and re.search(r'\b(ongkir|pengiriman|bisa kirim|bisa dikirim|kirim ke|antar ke)\b', text)
    if non_product or shipping:
        return {**skip('non_product_intent'), 'focus': list(focus)}
    if not explicit:
        return skip('image_not_requested')
    if ambiguous:
        return skip('ambiguous_product')
    if not targets:
        return skip('no_product')
    evidenced = set()
    for passage in evidence:
        for line in passage.splitlines():
            evidenced.update(products(line, assets))
    if not set(targets) <= evidenced:
        return skip('no_product_evidence')
    requested_variants = {key for key, terms in _VARIANTS.items() if any(contains(text, t) for t in terms)}
    metadata_variants = {term for term in variant_terms(assets, targets) if contains(text, term)}
    # Dimension and paper-weight requests require an actually depicted label.
    requested_labels = [normalized(m.group()) for m in re.finditer(
        r'\b\d+(?:[.,]\d+)?\s*(?:[x×]\s*\d+(?:[.,]\d+)?(?:\s*(?:cm|mm|m))?|gsm|cm|mm|ml|liter|lembar|ply|sisi)\b',
        question.lower())]
    candidates = []
    eligible = [a for a in assets if a.get('enabled')]
    prefer_hero = not comparison and not requested_variants and not metadata_variants and not requested_labels
    for a in eligible:
        if not set(targets) <= set(a['covered_product_types']):
            continue
        is_comparison = a['role'].endswith('comparison')
        if detail and not comparison and a['role'] != 'finishing_detail':
            continue
        if prefer_hero and is_comparison:
            continue
        if len(targets) > 1 and not is_comparison:
            continue
        if comparison and not is_comparison:
            continue
        depicted = normalized(' '.join(a.get('depicted_variants', [])))
        if any(not contains(depicted, term) for term in metadata_variants):
            continue
        if any(not any(contains(depicted, t) for t in _VARIANTS[key]) for key in requested_variants):
            continue
        if any(label not in depicted for label in requested_labels):
            continue
        positive = sum(contains(text, term) for term in a.get('retrieval_keywords', []))
        negative = sum(contains(text, term) for term in a.get('negative_retrieval_keywords', []))
        preference = (0 if comparison == is_comparison else 1,
                      0 if a['role'] == 'hero' else 1, negative - positive, a['asset_id'])
        candidates.append((preference, a))
    if not candidates:
        return skip('variant_not_depicted' if requested_variants or metadata_variants or requested_labels else 'no_matching_asset')
    chosen = sorted(candidates, key=lambda item: item[0])[0][1]
    return {**result, 'asset': chosen, 'reason': 'explicit_comparison' if comparison else 'explicit_example'}
