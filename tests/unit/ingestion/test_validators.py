import pytest

from app.ingestion.exceptions import (
    DocumentTooLargeError,
    InvalidDocumentError,
    UnsupportedFileTypeError,
)
from app.ingestion.validators import validate_document


def test_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeError):
        validate_document(
            filename="malicious.exe",
            content=b"some content",
        )

def test_rejects_empty_file():
    with pytest.raises(InvalidDocumentError):
        validate_document(
            filename="document.pdf",
            content=b"",
        )

def test_rejects_invalid_pdf_signature():
    # MIME detection is checked first.
    with pytest.raises(UnsupportedFileTypeError):
        validate_document(
            filename="document.pdf",
            content=b"not a pdf document",
        )

def test_rejects_oversized_file():
    with pytest.raises(DocumentTooLargeError):
        validate_document(
            filename="document.pdf",
            content=b"%PDF-" + b"a" * (20 * 1024 * 1024),
        )

def test_rejects_mismatched_extension():
    with pytest.raises(UnsupportedFileTypeError):
        validate_document(
            filename="document.pdf",
            content=b"Hello, this is plain text.",
        )