import pytest

from app.backend.product_intent import ProductIntent, requires_knowledge


@pytest.mark.parametrize('question,action,products,resolution', [
    ('Boleh kirim gambar roll up?', 'show', ['roll-up-banner'], 'resolved'),
    ('Nomor admin berapa?', 'none', [], 'resolved'),
    ('Halo, saya mau harga banner', 'none', [], 'resolved'),
    ('Apa bedanya ketujuh kertas itu?', 'none', [], 'resolved'),
    ('Yang itu?', 'none', [], 'ambiguous'),
])
def test_business_evidence_cannot_be_disabled_by_intent(question, action, products, resolution):
    intent = ProductIntent(action=action, product_ids=products, view='hero', attributes=[],
        exact_visual=False, resolution=resolution, clarification='', changes_product=False,
        needs_knowledge=False)
    assert requires_knowledge(question, intent)


@pytest.mark.parametrize('question', ['Halo adminn', 'Selamat sore, Kak!', 'Terima kasih ya', 'Sip'])
def test_pure_social_message_can_skip_evidence(question):
    intent = ProductIntent(action='none', product_ids=[], view='hero', attributes=[],
        exact_visual=False, resolution='resolved', clarification='', changes_product=False,
        needs_knowledge=False)
    assert not requires_knowledge(question, intent)
