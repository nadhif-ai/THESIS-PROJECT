from langchain_core.documents import Document
from fastapi.testclient import TestClient

from app.admin.chunking import Chunking, split_document
from app.admin import global_knowledge, store


def test_separator_heading_does_not_replace_source_title_or_prices():
    source = Document(
        page_content=(
            "# Daftar harga produk cetak\n"
            "# -----------------------------------------------------------------------\n\n"
            "## Spanduk meteran\n"
            "Flexi China 280 GSM: Rp 16.500 per m².\n"
            "Panjang × lebar × harga per m²; bulatkan ke kelipatan Rp 500.\n"
            "## X-Banner dengan rangka\n"
            "Ukuran 60 × 160 cm: Rp 50.000 per paket.\n"
        ),
        metadata={"source": "prices.txt"},
    )

    chunks = split_document(source, Chunking())

    assert len(chunks) == 2
    assert chunks[0].metadata["section_1"] == "Daftar harga produk cetak"
    assert chunks[0].metadata["section_2"] == "Spanduk meteran"
    assert "Rp 16.500 per m²." in chunks[0].page_content
    assert "Panjang × lebar × harga per m²" in chunks[0].page_content
    assert chunks[1].metadata["section_1"] == "Daftar harga produk cetak"
    assert "Ukuran 60 × 160 cm: Rp 50.000 per paket." in chunks[1].page_content
    assert all(chunk.metadata["source"] == "prices.txt" for chunk in chunks)
    assert "# -----------------------------------------------------------------------" in source.page_content


def test_source_chunking_respects_frozen_preprocessing_version():
    source = {
        "name": "prices.txt",
        "format": "txt",
        "pages": [{"text": "# Harga\n# ---\n## Spanduk\nRp 16.500 per m²."}],
    }

    historical = global_knowledge.documents(
        source,
        {"chunk_size": 1000, "chunk_overlap": 100, "preprocessing": "sections-v1"},
    )
    corrected = global_knowledge.documents(
        source,
        {"chunk_size": 1000, "chunk_overlap": 100, "preprocessing": "sections-v2"},
    )

    assert historical[0].metadata["section_1"] == "---"
    assert corrected[0].metadata["section_1"] == "Harga"
    assert "Rp 16.500 per m²." in historical[0].page_content
    assert "Rp 16.500 per m²." in corrected[0].page_content


def test_chunking_configuration_stages_current_recipe_with_auth_and_csrf(pg_live):
    from app.main import app

    salt = "00" * 16
    with pg_live.admin_connection() as db:
        db.execute(
            "INSERT INTO chatbot.users VALUES(%s,%s,%s)",
            ("admin", salt, store.hash_password("local-test-password", salt)),
        )
    client = TestClient(app)
    config = {"chunk_size": 900, "chunk_overlap": 90}
    assert client.put("/admin/api/knowledge/chunking", json=config).status_code == 401
    login = client.post(
        "/admin/api/login",
        json={"username": "admin", "password": "local-test-password"},
    )
    assert login.status_code == 200
    assert client.put("/admin/api/knowledge/chunking", json=config).status_code == 403
    headers = {"x-csrf-token": login.json()["csrf"]}

    saved = client.put("/admin/api/knowledge/chunking", json=config, headers=headers)
    catalog = client.get("/admin/api/knowledge")

    assert saved.status_code == 200
    assert catalog.status_code == 200
    assert catalog.json()["chunking"] == {**config, "preprocessing": "sections-v2"}
    assert catalog.json()["pending"] is True
    assert catalog.json()["active"] is None
    invalid = client.put(
        "/admin/api/knowledge/chunking",
        json={"chunk_size": 600, "chunk_overlap": 350},
        headers=headers,
    )
    assert invalid.status_code == 400
    assert client.get("/admin/api/knowledge").json()["chunking"] == catalog.json()["chunking"]
