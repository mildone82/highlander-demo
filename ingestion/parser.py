"""Document parsing for the ingestion worker.

Text/Markdown are decoded natively. PDF and DOCX are parsed when the optional
libraries are installed (see ``requirements-ingestion.txt``); legacy ``.doc`` is
rejected with a clear message because it needs a different parser.
"""

from __future__ import annotations

import io
import os
from typing import List


class UnsupportedDocumentError(ValueError):
    """Raised when a document cannot be parsed with the installed libraries."""


_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".json", ".csv", ".log", ".html", ".htm"}


def parse_document(key: str, data: bytes) -> str:
    ext = os.path.splitext(key)[1].lower()
    if ext == ".pdf":
        return _parse_pdf(data)
    if ext == ".docx":
        return _parse_docx(data)
    if ext == ".doc":
        raise UnsupportedDocumentError(
            "legacy .doc is not supported; convert it to .docx or .pdf before ingestion"
        )
    return _decode_text(data)


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _parse_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - exercised only without pypdf installed
        raise UnsupportedDocumentError("pypdf is required to parse PDF documents") from exc

    reader = PdfReader(io.BytesIO(data))
    pages: List[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def _parse_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError as exc:  # pragma: no cover - exercised only without python-docx installed
        raise UnsupportedDocumentError("python-docx is required to parse DOCX documents") from exc

    document = docx.Document(io.BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
