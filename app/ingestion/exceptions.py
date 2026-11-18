class IngestionError(Exception):
    """Base exception for document ingestion errors."""

class UnsupportedFileTypeError(IngestionError):
    """Raised when a document format is unsupported."""

class InvalidDocumentError(IngestionError):
    """Raised when a document is malformed or unreadable."""

class DocumentTooLargeError(IngestionError):
    """Raised when an uploaded document exceeds the size limit."""

class EmptyDocumentError(IngestionError):
    """Raised when no usable text can be extracted."""

class DocumentParsingError(IngestionError):
    """Raised when document parsing fails."""

class ChunkingError(IngestionError):
    """Raised when document chunking fails."""

    