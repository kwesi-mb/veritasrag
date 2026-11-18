from functools import lru_cache

from app.core.config import settings
from app.ingestion.chunker import DocumentChunker
from app.ingestion.parsers import DocumentParser
from app.ingestion.service import DocumentIngestionService
from app.ingestion.tokenizer import DocumentTokenizer


@lru_cache
def get_document_tokenizer() -> DocumentTokenizer:
    return DocumentTokenizer(
        model_name=settings.embedding_model
    )

def get_ingestion_service() -> DocumentIngestionService:
    tokenizer = get_document_tokenizer()

    chunker = DocumentChunker(
        tokenizer=tokenizer,
        chunk_size=512,
        chunk_overlap=64,
    )

    return DocumentIngestionService(
        parser=DocumentParser(),
        chunker=chunker,
    )