from app.backend.catalog_selection import select
from testing.test_product_catalog import record


def test_first_price_question_attaches_then_same_product_quantity_does_not():
    asset = record()
    result = select('Harga roll up berapa?', [asset], ['Roll up banner tersedia. Harga sesuai ukuran.'])
    assert result['asset']['asset_id'] == 'roll-up-hero'
    followup = select('Kalau 5 pcs?', [asset], ['Roll up banner tersedia.'], focus=['roll-up-banner'])
    assert followup['asset'] is None
    assert followup['reason'] == 'same_product_followup'


def test_ambiguous_sticker_and_unpictured_variant_skip():
    assert select('Harga stiker?', [record()], ['Stiker tersedia.'])['reason'] == 'ambiguous_product'
    assert select('Contoh roll up transparan', [record()], ['Roll up banner tersedia.'])['reason'] == 'variant_not_depicted'


def test_topic_change_requires_new_product_evidence():
    assert select('Harga roll up', [record()], ['X banner tersedia.'], focus=['x-banner'])['reason'] == 'no_product_evidence'
    assert select('Harga roll up', [record()], ['Roll up banner tersedia.'], focus=['x-banner'])['asset']


def test_duplicate_suppression_and_explicit_resend():
    assert select('Harga roll up', [record()], ['Roll up banner'], seen={'roll-up-hero'})['reason'] == 'already_attempted'
    result = select('Kirim contoh itu lagi', [record()], ['Roll up banner'], focus=['roll-up-banner'], seen={'roll-up-hero'})
    assert result['asset'] and result['explicit']


def test_full_roll_up_name_does_not_resolve_generic_banner_too():
    assert select('Harga roll up banner?', [record()], ['Roll up banner tersedia.'])['asset']


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
        decision=select(question,assets,[question])
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
