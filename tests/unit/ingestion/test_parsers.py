from io import BytesIO

import fitz
import pytest
from docx import Document as DocxDocument

from app.ingestion.exceptions import (
    DocumentParsingError,
    EmptyDocumentError,
)
from app.ingestion.parsers import DocumentParser


def test_parse_txt_document():
    parser = DocumentParser()

    result = parser.parse(
        filename="research.txt",
        file_type="txt",
        content=b"VeritasRAG is a hybrid RAG engine.",
    )

    assert result.file_type == "txt"
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "hybrid RAG engine" in result.pages[0].content 

def test_parse_invalid_utf8():
    parser = DocumentParser()

    with pytest.raises(DocumentParsingError):
        parser.parse(
            filename="research.txt",
            file_type="txt",
            content=b"\xff\xfe\xfa",
        )

def test_parse_empty_document():
    parser = DocumentParser()

    with pytest.raises(EmptyDocumentError):
        parser.parse(
            filename="empty.txt",
            file_type="txt",
            content=b"   ",
        )

def test_parse_pdf():
    parser = DocumentParser()

    buffer = BytesIO()

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "VeritasRAG PDF testing")

    pdf.save(buffer)
    pdf.close()

    result = parser.parse(
        filename="research.pdf",
        file_type="pdf",
        content=buffer.getvalue(),
    )

    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "VeritasRAG" in result.pages[0].content

def test_parse_docx():
    parser = DocumentParser()

    buffer = BytesIO()

    document = DocxDocument()
    document.add_paragraph("VeritasRAG DOCX testing")
    document.save(buffer)

    result = parser.parse(
        filename="research.docx",
        file_type="docx",
        content=buffer.getvalue(),
    )

    assert len(result.pages) == 1
    assert "VeritasRAG DOCX testing" in result.pages[0].content