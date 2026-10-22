from app.backend.catalog_selection import select
from testing.test_product_catalog import record


def test_price_and_quantity_questions_do_not_attach_images():
    for question in ('Harga roll up berapa?', 'Kalau 5 pcs?', 'Bedanya bahan roll up apa?'):
        result = select(question, [record()], ['Roll up banner tersedia.'], focus=['roll-up-banner'])
        assert result['asset'] is None and result['reason'] == 'image_not_requested'


def test_ambiguous_sticker_and_unpictured_variant_skip():
    assert select('Gambar stiker?', [record()], ['Stiker tersedia.'])['reason'] == 'ambiguous_product'
    assert select('Contoh roll up transparan', [record()], ['Roll up banner tersedia.'])['reason'] == 'variant_not_depicted'


def test_topic_change_requires_new_product_evidence():
    assert select('Gambar roll up', [record()], ['X banner tersedia.'], focus=['x-banner'])['reason'] == 'no_product_evidence'
    assert select('Gambar roll up', [record()], ['Roll up banner tersedia.'], focus=['x-banner'])['asset']


def test_duplicate_suppression_and_explicit_resend():
    assert select('Gambar roll up', [record()], ['Roll up banner'], seen={'roll-up-hero'})['asset']
    result = select('Kirim contoh itu lagi', [record()], ['Roll up banner'], focus=['roll-up-banner'], seen={'roll-up-hero'})
    assert result['asset'] and result['explicit']


def test_full_roll_up_name_does_not_resolve_generic_banner_too():
    assert select('Gambar roll up banner?', [record()], ['Roll up banner tersedia.'])['asset']


def test_software_inquiry_does_not_trigger_product_image():
    assert select('Software desain roll up apa?', [record()], ['Roll up banner tersedia.'])['reason']=='non_product_intent'


def test_real_seed_covers_all_products_and_comparison_without_hero_substitution():
    import json
    from pathlib import Path
    data=json.loads(Path('dataset/image-product/manifest.json').read_text())
    assets=[{**a,'asset_id':a['id'],'enabled':True,
             'covered_product_types':['x-banner','y-banner','roll-up-banner'] if a['product_type']=='standing-banner-comparison' else [a['product_type']]}
            for a in data['assets']]
    questions={
        'banner-spanduk-hero':'Harga spanduk?', 'stiker-meteran-hero':'Harga stiker meteran?',
        'x-banner-hero':'Harga X-banner?', 'y-banner-hero':'Harga Y-banner?', 'roll-up-banner-hero':'Harga roll up banner?',
        'stiker-a3-plus-hero':'Harga stiker A3?', 'digital-print-a3-plus-hero':'Harga digital print A3?',
        'id-card-hero':'Harga ID card?', 'kartu-nama-hero':'Harga kartu nama?',
        'brosur-flyer-hero':'Harga brosur?', 'nota-ncr-hero':'Harga nota NCR?', 'stempel-otomatis-hero':'Harga stempel?',
        'poster-albatros-hero':'Harga poster?', 'kalender-meja-a5-hero':'Harga kalender?', 'e-money-custom-uv-hero':'Harga e-money?',
        'plakat-akrilik-hero':'Harga plakat?', 'yasin-buku-saku-hero':'Harga Yasin?', 'tumbler-custom-hero':'Harga tumbler?',
        'pin-aksesoris-hero':'Harga pin?', 'lanyard-custom-hero':'Harga lanyard?', 'korek-api-custom-hero':'Harga korek api?',
        'standing-banner-form-comparison':'Bedanya X-banner, Y-banner dan roll up banner?',
        'banner-spanduk-material-comparison':'Bedanya bahan spanduk china dan korea?',
        'stiker-meteran-material-comparison':'Bedanya stiker meteran OWV dan transparan?',
        'digital-print-a3-plus-paper-comparison':'Bedanya digital print Art Paper dan HVS?',
        'kartu-nama-glossy-doff-comparison':'Bedanya kartu nama glossy dan doff?',
    }
    for expected,question in questions.items():
        decision=select('Lihat gambarnya: '+question,assets,[question])
        assert decision['asset'] and decision['asset']['asset_id']==expected, (question,decision)
    duplicate=select('Harga roll up banner?',assets,['Roll up banner tersedia.'],seen={'roll-up-banner-hero'})
    assert duplicate['asset'] is None


def test_explicit_kiss_cut_visual_uses_detail():
    hero={**record(),'asset_id':'kiss-hero','product_type':'stiker-a3-kiss-cut','covered_product_types':['stiker-a3-kiss-cut'],'aliases':[]}
    detail={**hero,'asset_id':'kiss-detail','role':'finishing_detail'}
    result=select('Contoh detail kiss cut', [hero,detail], ['Stiker A3 kiss cut tersedia.'])
    assert result['asset']['asset_id']=='kiss-detail'


def test_source_only_variants_and_shipping_do_not_get_false_visual_confirmation():
    assets=[{**record(),'asset_id':'id-card-hero','product_type':'id-card','covered_product_types':['id-card'],
             'aliases':[],'source_only_variants':['ID Card PVC','ID Card UV'],
             'depicted_variants':['Representative product appearance; exact source variant not visually authenticated']},
            {**record(),'asset_id':'stiker-a3-hero','product_type':'stiker-a3-kiss-cut','covered_product_types':['stiker-a3-kiss-cut'],
             'aliases':[],'source_only_variants':['Vinyl tanpa Kiss Cut'],'depicted_variants':[]}]
    for question in ('Contoh ID card UV','Contoh ID card PVC','Contoh stiker A3 vinyl'):
        assert select(question,assets,[question])['reason']=='variant_not_depicted'
    decision=select('Roll up banner bisa kirim ke Bandung?', [record()], ['Roll up banner tersedia.'],focus=['roll-up-banner'],seen=['roll-up-hero'])
    assert decision['asset'] is None and not decision['explicit']


def test_source_only_paper_formats_and_numeric_sizes_are_not_depicted():
    import json
    from pathlib import Path
    data=json.loads(Path('dataset/image-product/manifest.json').read_text())
    assets=[{**a,'asset_id':a['id'],'enabled':True,
        'covered_product_types':['x-banner','y-banner','roll-up-banner'] if a['product_type']=='standing-banner-comparison' else [a['product_type']]}
        for a in data['assets']]
    for question in ('Contoh poster A0','Contoh poster A1','Contoh brosur A4','Contoh pin 5.8 cm'):
        assert select(question,assets,[question])['reason']=='variant_not_depicted'


def test_request_only_screenshot_conversation_and_repeated_visual_requests():
    banner={**record(),'asset_id':'banner-hero','product_type':'banner-spanduk','covered_product_types':['banner-spanduk'],'aliases':[]}
    stand={**record(),'asset_id':'x-hero','product_type':'x-banner','covered_product_types':['x-banner'],'aliases':[]}
    assets=[banner,stand]; evidence=['Banner spanduk tersedia. X-banner tersedia.']
    first=select('Hi kak mau print banner dong',assets,evidence)
    assert first['asset'] is None and first['reason']=='image_not_requested'
    second=select('Mau liat yg banner x tegak',assets,evidence,focus=first['focus'])
    assert second['asset']['asset_id']=='x-hero'
    third=select('Iyaa kak X-banner, kirimin preview gambarnya dulu dong',assets,evidence,focus=second['focus'],seen=['x-hero'])
    assert third['asset']['asset_id']=='x-hero' and third['reason']=='explicit_example'


def test_negated_and_price_only_view_wording_never_requests_media():
    for question in (
        'Gambarnya jangan dikirim ya', 'Tidak perlu foto, harga saja',
        'Jangan lihat lagi, berapa harga roll up?', 'Jangan kasih contoh roll up',
        'Mau lihat harga roll up', 'Bisa liat daftar harga roll up?',
        'Contoh perhitungan roll up berapa?', 'Teks saja, tanpa gambar roll up',
    ):
        decision = select(question, [record()], ['Roll up banner tersedia.'], focus=['roll-up-banner'])
        assert decision['asset'] is None and not decision['explicit'], question


def test_contextual_requests_and_successive_products_can_repeat():
    other = {**record(), 'asset_id': 'x-hero', 'product_type': 'x-banner',
             'covered_product_types': ['x-banner'], 'aliases': []}
    assets = [record(), other]
    focus, seen = [], []
    for question, expected in (
        ('Preview roll up', 'roll-up-hero'), ('Fotonya banner x', 'x-hero'),
        ('Liat roll up lagi', 'roll-up-hero'), ('Kirim itu lagi', 'roll-up-hero'),
    ):
        decision = select(question, assets, ['Roll up banner dan X-banner tersedia.'], focus=focus, seen=seen)
        assert decision['asset']['asset_id'] == expected
        focus = decision['focus']; seen.append(expected)


def test_photo_printing_and_examples_of_specifications_are_not_visual_requests():
    asset = {**record(), 'product_type': 'digital-print-a3',
             'covered_product_types': ['digital-print-a3'], 'aliases': []}
    for question in ('Harga digital print A3 untuk foto berapa?', 'Harga cetak foto digital print A3?',
                     'Tolong contoh ukuran roll up apa saja?'):
        decision = select(question, [asset, record()], [question])
        assert decision['asset'] is None and not decision['explicit'], question


def test_artwork_requirements_and_negation_with_product_do_not_attach():
    banner = {**record(), 'product_type': 'banner-spanduk', 'covered_product_types': ['banner-spanduk'], 'aliases': []}
    for question in ('File gambar spanduk harus format apa?', 'Resolusi foto untuk banner harus berapa?',
                     'Fotonya roll up jangan dikirim, harga saja'):
        decision = select(question, [banner, record()], ['Banner spanduk dan roll up banner tersedia.'])
        assert decision['asset'] is None and not decision['explicit'], question
    assert select('Kirim gambar roll up tanpa laminasi', [record()], ['Roll up banner tersedia.'])['explicit']
