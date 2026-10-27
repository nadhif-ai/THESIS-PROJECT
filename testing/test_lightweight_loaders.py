from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.backend.loader import _load_csv_file, load_pdf_pages


def test_csv_preserves_quoted_text_bom_strings_and_skips_invalid_rows(tmp_path):
    source = tmp_path / "knowledge.csv"
    source.write_text(
        '\ufeffdoc_id, title ,body,media_url\n'
        '001,"Harga, kartu","Baris pertama\nBaris kedua",https://example.com/a.png\n'
        '002,NA,NULL,\n'
        '003,,No title,\n'
        '004,Too,many,,columns\n'
        '005,Missing body\n'
        '\n',
        encoding="utf-8",
    )
    docs = _load_csv_file(source)
    assert [doc.metadata["id"] for doc in docs] == ["001", "002", "005"]
    assert docs[0].page_content == "Pertanyaan: Harga, kartu\nJawaban: Baris pertama\nBaris kedua"
    assert docs[0].metadata["media_url"] == "https://example.com/a.png"
    assert docs[1].page_content == "Pertanyaan: NA\nJawaban: NULL"
    assert docs[2].page_content == "Pertanyaan: Missing body\nJawaban: None"


def test_pdf_preserves_page_text_labels_and_document_metadata(tmp_path):
    source = tmp_path / "knowledge.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)}),
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 100 Td (Harga Rp 5000) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": " Price list ", "/CreationDate": "D:20261025100000+07'00'"})
    writer.write(source)
    docs = load_pdf_pages(source)
    assert [doc.page_content for doc in docs] == ["Harga Rp 5000", ""]
    assert [doc.metadata["page"] for doc in docs] == [0, 1]
    assert [doc.metadata["page_label"] for doc in docs] == ["1", "2"]
    assert docs[0].metadata["title"] == "Price list"
    assert docs[0].metadata["creationdate"] == "2026-10-25T10:00:00+07:00"
    assert docs[0].metadata["total_pages"] == 2
    assert docs[0].metadata["source"] == str(source)
