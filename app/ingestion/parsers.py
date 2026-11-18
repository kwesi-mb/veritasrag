from dataclasses import dataclass
from io import BytesIO

import fitz
from docx import Document as DocxDocument

from app.ingestion.exceptions import (
    DocumentParsingError,
    EmptyDocumentError,
)


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    content: str

@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    file_type: str
    pages: list[ParsedPage]

class DocumentParser:

    def parse(
        self,
        filename: str,
        file_type: str,
        content: bytes,
    ) -> ParsedDocument:

        try:
            if file_type == "pdf":
                pages = self._parse_pdf(content)

            elif file_type == "docx":
                pages = self._parse_docx(content)

            elif file_type in {"txt", "md"}:
                pages = self._parse_text(content)

            else:
                raise DocumentParsingError(
                    f"Unsupported document type: {file_type}"
                )

        except DocumentParsingError:
            raise

        except Exception as exc:
            raise DocumentParsingError(
                f"Failed to parse {filename}"
            ) from exc 

        if not any(page.content.strip() for page in pages):
            raise EmptyDocumentError(
                "No extractable text found in document."
            )

        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            pages=pages,
        )

    @staticmethod
    def _parse_pdf(content: bytes) -> list[ParsedPage]:
        pages = []

        with fitz.open(
            stream=content,
            filetype="pdf",
        ) as pdf:

            for index, page in enumerate(pdf):
                pages.append(
                    ParsedPage(
                        page_number=index + 1,
                        content=page.get_text("text"),
                    )
                )

        return pages

    @staticmethod
    def _parse_docx(content: bytes) -> list[ParsedPage]:
        document = DocxDocument(BytesIO(content))

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        tables = []

        for table in document.tables:
            for row in table.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells 
                ]

                tables.append(" | ".join(cells))

        extracted = "\n".join(paragraphs + tables)

        return [
            ParsedPage(
                page_number=1,
                content=extracted,
            )
        ]

    @staticmethod
    def _parse_text(content:bytes) -> list[ParsedPage]:
        try:
            extracted = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentParsingError(
                "Text document must use UTF-8 encoding."
            ) from exc

        return [
            ParsedPage(
                page_number=1,
                content=extracted,
            )
        ]