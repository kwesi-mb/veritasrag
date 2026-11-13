import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Document, DocumentChunk


@pytest.mark.asyncio
async def test_create_documenet(db_session):
    document = Document(
        filename="rag_research.pdf",
        file_type="pdf",
        content_hash=uuid.uuid4().hex + "a" * 32,
        file_size_bytes=102400,
    )

    db_session.add(document)
    await db_session.commit()

    result = await db_session.execute(
        select(Document).where(
            Document.id == document.id 
        )
    )

    saved_document = result.scalar_one()

    assert saved_document.filename == "rag_research.pdf"
    assert saved_document.status == "pending"
    assert saved_document.version == 1
    assert saved_document.created_at is not None

@pytest.mark.asyncio
async def test_document_chunk_persistance(db_session):
    document = Document(
        filename="research.pdf",
        file_type="pdf",
        content_hash=uuid.uuid4().hex + "b" * 32,
        file_size_bytes=2048, 
    )

    db_session.add(document)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        document_version=1,
        chunk_index=0,
        content="Hybrid retrieval combines dense and sparse search.",
        token_count=10,
        page_number=1,
        embedding=[0.1] * 768,
        chunk_metadata={"section": "Introduction"},
    )

    db_session.add(chunk)
    await db_session.commit()

    result =  await db_session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == document.id 
        )
    )

    saved_chunk = result.scalar_one()

    assert saved_chunk.content == (
        "Hybrid retrieval combines dense and sparse search."
    )
    assert saved_chunk.chunk_index == 0
    assert saved_chunk.embedding is not None
    assert len(saved_chunk.embedding) == 768
    assert saved_chunk.search_vector is not None

@pytest.mark.asyncio
async def test_duplicate_document_hash_rejected(db_session):
    content_hash = uuid.uuid4().hex + "c" * 32

    first = Document(
        filename="first.pdf",
        file_type="pdf",
        content_hash=content_hash,
        file_size_bytes=1024,
    )

    second = Document(
        filename="second.pdf",
        file_type="pdf",
        content_hash=content_hash,
        file_size_bytes=2048,
    )

    db_session.add(first)
    await db_session.commit()

    db_session.add(second)

    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_chunk_cascades_when_document_deleted(db_session):
    document = Document(
        filename="delete_me.pdf",
        file_type="pdf",
        content_hash=uuid.uuid4().hex + "d" * 32,
        file_size_bytes=1024,
    )

    db_session.add(document)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        document_version=1,
        chunk_index=0,
        content="This chunk should be deleted.",
        token_count=6,
    )

    db_session.add(chunk)
    await db_session.commit()

    chunk_id = chunk.id 

    await db_session.delete(document)
    await db_session.commit()

    result = await db_session.execute(
        select(DocumentChunk).where(
            DocumentChunk.id == chunk_id
        )
    )

    assert result.scalar_one_or_none() is None 