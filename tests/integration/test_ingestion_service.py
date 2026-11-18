
import pytest
from sqlalchemy import func, select

from app.ingestion.chunker import DocumentChunker
from app.ingestion.parsers import DocumentParser
from app.ingestion.service import DocumentIngestionService
from app.models import Document, DocumentChunk


class FakeTokenizer:

    def encode(self, text: str) -> list[int]:
        return list(range(len(text.split())))

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(
            f"token_{token_id}"
            for token_id in token_ids 
        ) 

    def special_token_count(self) -> int:
        return 2

@pytest.fixture
def ingestion_service():
    tokenizer = FakeTokenizer()

    chunker = DocumentChunker(
        tokenizer=tokenizer,
        chunk_size=20,
        chunk_overlap=4,
    )

    return DocumentIngestionService(
        parser=DocumentParser(),
        chunker=chunker,

    )

@pytest.mark.asyncio
async def test_ingest_document(
    db_session,
    ingestion_service,
):
    content = (
        b"VeritasRAG combines dense retrieval "
        b"with sparse retrieval."
    )

    result = await ingestion_service.ingest(
        session=db_session,
        filename="research.txt",
        content=content,
    )

    assert result.status == "processed"
    assert result.total_chunks >= 1
    assert result.already_exists is False 

    document = await db_session.scalar(
        select(Document).where(
            Document.id == result.document_id 
        )
    )

    assert document is not None
    assert document.filename == "research.txt"

    count = await db_session.scalar(
        select(func.count(DocumentChunk.id)).where(
            DocumentChunk.document_id == document.id
        )
    )

    assert count == result.total_chunks

@pytest.mark.asyncio
async def test_duplicate_ingestion_is_idempotent(
    db_session,
    ingestion_service,
):
    content = b"Same document content for testing."

    first = await ingestion_service.ingest(
        session=db_session,
        filename="first.txt",
        content=content,
    )

    second = await ingestion_service.ingest(
        session=db_session,
        filename="second.txt",
        content=content,
    )

    assert first.document_id == second.document_id
    assert first.content_hash == second.content_hash
    assert second.already_exists is True

    count = await db_session.scalar(
        select(func.count(Document.id))
    )

    assert count == 1

@pytest.mark.asyncio
async def test_different_content_creates_different_documents(
    db_session,
    ingestion_service,
):
    first = await ingestion_service.ingest(
        session=db_session,
        filename="first.txt",
        content=b"First document.",
    )

    second = await ingestion_service.ingest(
        session=db_session,
        filename="second.txt",
        content=b"Second document."
    )

    assert first.document_id != second.document_id