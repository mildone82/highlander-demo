import io

from ingestion.parser import UnsupportedDocumentError, parse_document


def test_parse_utf8_text():
    assert parse_document("note.txt", "你好，世界".encode("utf-8")) == "你好，世界"


def test_parse_gb18030_text():
    assert parse_document("note.txt", "中文文档".encode("gb18030")) == "中文文档"


def test_parse_docx():
    import docx

    document = docx.Document()
    document.add_paragraph("Hello 世界")
    buffer = io.BytesIO()
    document.save(buffer)

    text = parse_document("doc.docx", buffer.getvalue())
    assert "Hello 世界" in text


def test_parse_pdf_blank_page_does_not_crash():
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)

    assert parse_document("doc.pdf", buffer.getvalue()) == ""


def test_parse_legacy_doc_is_rejected():
    try:
        parse_document("legacy.doc", b"not really a doc")
    except UnsupportedDocumentError:
        return
    raise AssertionError("expected UnsupportedDocumentError for legacy .doc")
