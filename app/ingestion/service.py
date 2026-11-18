import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.chunker import DocumentChunker
from app.ingestion.exceptions import IngestionError
from app.ingestion.parsers import DocumentParser
from app.ingestion.validators import validate_document
from app.models import Document, DocumentChunk


@dataclass(frozen=True)
class IngestionResult:
    document_id: uuid.UUID
    filename: str
    content_hash: str
    total_chunks: int
    status: str
    already_exists: bool = False 

class DocumentIngestionService:

    def __init__(
        self,
        parser: DocumentParser,
        chunker: DocumentChunker,
    ):
        self.parser = parser
        self.chunker = chunker


    async def ingest(
        self,
        session: AsyncSession,
        filename: str,
        content: bytes,
    ) -> IngestionResult:

        file_type = validate_document(
            filename=filename,
            content=content,
        )

        content_hash = hashlib.sha256(
            content 
        ).hexdigest()

        # Check whether identical content already exists.
        existing = await session.scalar(
            select(Document).where(
                Document.content_hash == content_hash 
            )
        )

        if existing:
            return IngestionResult(
                document_id=existing.id,
                filename=existing.filename,
                content_hash=existing.content_hash,
                total_chunks=await self._count_chunks(
                    session,
                    existing.id,
                ),
                status=existing.status,
                already_exists=True,
            )

        parsed = self.parser.parse(
            filename=filename,
            file_type=file_type,
            content=content,
        )

        chunks = self.chunker.chunk_pages(
            parsed.pages
        )

        if not chunks:
            raise IngestionError(
                "Document produced no usable chunks."
            )

        document = Document(
            filename=filename,
            file_type=file_type,
            content_hash=content_hash,
            file_size_bytes=len(content),
            version=1,
            status="pending",
        )

        try:
            session.add(document)
            await session.flush()

            chunk_records = [
                DocumentChunk(
                    document_id=document.id,
                    document_version=document.version,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    page_number=chunk.page_number,
                    chunk_metadata=chunk.metadata,
                )
                for chunk in chunks 
            ]

            session.add_all(chunk_records)

            document.status = "processed"

            await session.commit()

            return IngestionResult(
                document_id=document.id,
                filename=document.filename,
                content_hash=content_hash,
                total_chunks=len(chunks),
                status=document.status,
            )

        except IntegrityError:
            await session.rollback()

            # Another request may have inserted identical
            # content concurrently.
            existing = await session.scalar(
                select(Document).where(
                    Document.content_hash == content_hash
                )
            )

            if existing:
                return IngestionResult(
                    document_id=existing.id,
                    filename=existing.filename,
                    content_hash=existing.content_hash,
                    total_chunks=await self._count_chunks(
                        session,
                        existing.id,
                    ),
                    status=existing.status,
                    already_exists=True,
                )

            raise

        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def _count_chunks(
        session: AsyncSession,
        document_id: uuid.UUID,
    ) -> int:
        from sqlalchemy import func

        count = await session.scalar(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id
            )
        )

        return count or 0