import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.backend.history import retrieval_question


@pytest.mark.parametrize("question", [
    "Boleh minta pin lokasi gerai?",
    "Alamat fisik cabang yang di Pamulang di mana?",
    "Lokasi gerai terdekat dari Ciputat?",
    "Alamat email untuk kirim desain ke cabang mana?",
    "Nomor WhatsApp cabang berapa?",
])
def test_location_and_contact_questions_do_not_invent_an_ordering_task(question):
    assert retrieval_question(question, []) == question


def test_explicit_order_handoff_still_retrieves_branch_and_ordering_information():
    query = retrieval_question("Mau pesan stiker, saya lanjut ke toko", [])
    assert "Mau pesan stiker" in query
    assert "alamat" in query and "kontak admin" in query and "alur pemesanan" in query


@pytest.mark.parametrize("question", ["oke", "2", "Pamulang", "Saya pilih cabang Pamulang"])
def test_branch_selection_preserves_handoff_and_customer_specifications(question):
    history = [HumanMessage(content="Stiker vinyl 10 x 10 cm sebanyak 50 pcs"),
               AIMessage(content="Ringkasannya sudah siap. Pilih cabang: 1. Ciputat atau 2. Pamulang?")]
    query = retrieval_question(question, history)
    assert "alamat" in query and "kontak admin" in query and "alur pemesanan" in query
    assert "Stiker vinyl 10 x 10 cm sebanyak 50 pcs" in query


@pytest.mark.parametrize("question", ["Alamat email cabang berapa?", "Nomor WhatsApp admin berapa?",
                                      "Alamat fisik gerainya di mana?"])
def test_new_information_question_after_branch_offer_keeps_its_own_task(question):
    history = [HumanMessage(content="Saya cari gerai di Tangerang Selatan"),
               AIMessage(content="Ada cabang Ciputat dan Pamulang. Mau ke cabang mana?")]
    query = retrieval_question(question, history)
    assert query.startswith(question)
    assert "Saya cari gerai di Tangerang Selatan" not in query
    assert "alur pemesanan" not in query


def test_plain_material_followup_retains_previous_customer_product():
    query = retrieval_question("Vinyl saja", [HumanMessage(content="Butuh stiker untuk botol"),
                                              AIMessage(content="Pilih cromo atau vinyl?")])
    assert "Vinyl saja" in query and "Butuh stiker untuk botol" in query
    assert "alur pemesanan" not in query


def test_topic_switch_stops_unrelated_product_history():
    history = [HumanMessage(content='Roll up 60 x 160 cm 3 buah'), AIMessage(content='Siap.'),
               HumanMessage(content='Sekarang saya mau perbandingan tujuh kertas A3+'),
               AIMessage(content='Ini ilustrasinya.')]
    query = retrieval_question('Apa bedanya ketujuh kertas itu?', history)
    assert 'kertas A3+' in query and 'Roll up' not in query


def test_independent_shop_question_ignores_product_history():
    query = retrieval_question('Jam operasional toko berapa?', [HumanMessage(content='Roll up 3 buah')])
    assert query == 'Jam operasional toko berapa?'
