from pathlib import Path

import magic

from app.ingestion.exceptions import (
    DocumentTooLargeError,
    InvalidDocumentError,
    UnsupportedFileTypeError,
)

MAX_FILE_SIZE = 20 * 1024 * 1024 # 20MB

SUPPORTED_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".txt": {"text/plain"},
    ".md": {
        "text/plain",
        "text/markdown",
        "text/x-markdown",
    },
}

def validate_document(
    filename: str,
    content: bytes,
) -> str:
    """
    Validate an uploaded document.

    Returns:
        Normalized file extension.
    """

    if not filename or not filename.strip():
        raise InvalidDocumentError("Filename is required.")

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported file extension: {extension}"
        )

    if not content:
        raise InvalidDocumentError("Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise DocumentTooLargeError(
            "Document exceeds the 20 MB upload limit."
        )

    detected_mime = magic.from_buffer(
        content[:8192],
        mime=True,
    )

    allowed_mimes = SUPPORTED_TYPES[extension]

    if detected_mime not in allowed_mimes:
        raise UnsupportedFileTypeError(
            f"File content does not match {extension} format."
        )

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise InvalidDocumentError("Invalid PDF file signature.")

    if extension == ".docx":
        import zipfile
        from io import BytesIO

        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if "[Content_Types].xml" not in archive.namelist():
                    raise InvalidDocumentError(
                        "Invalid DOCX document structure."
                    )

                if "word/document.xml" not in archive.namelist():
                    raise InvalidDocumentError(
                        "DOCX document body is missing."
                    )

        except zipfile.BadZipFile as exc:
            raise InvalidDocumentError(
                "Invalid DOCX archive."
            ) from exc 

    return extension.lstrip(".")