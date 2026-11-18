from dataclasses import dataclass

from app.ingestion.exceptions import ChunkingError
from app.ingestion.normalizer import TextNormalizer
from app.ingestion.parsers import ParsedPage
from app.ingestion.tokenizer import DocumentTokenizer


@dataclass(frozen=True)
class DocumentChunkData:
    chunk_index: int
    content: str
    token_count: int
    page_number: int
    metadata: dict 

class DocumentChunker:

    def __init__(
        self,
        tokenizer: DocumentTokenizer,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        self.tokenizer = tokenizer
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        special_tokens = tokenizer.special_token_count()

        self.content_budget = chunk_size - special_tokens

        if self.content_budget <= 0:
            raise ValueError(
                "Chunk size is too small for tokenizer special tokens."
            )

        if chunk_overlap >= self.content_budget:
            raise ValueError(
                "Chunk overlap must be smaller than the content budget."
            )

    def chunk_pages(
        self,
        pages: list[ParsedPage],
    ) -> list[DocumentChunkData]:

        chunks = []
        chunk_index = 0

        try:
            for page in pages:
                normalized = TextNormalizer.normalize(
                    page.content
                )

                if not normalized:
                    continue

                token_ids = self.tokenizer.encode(
                    normalized
                )

                start = 0

                while start < len(token_ids):
                    end = min(
                        start + self.content_budget,
                        len(token_ids), 
                    )

                    chunk_tokens = token_ids[start:end]

                    chunk_text = self.tokenizer.decode(
                        chunk_tokens
                    ).strip()

                    if chunk_text:
                        chunks.append(
                            DocumentChunkData(
                                chunk_index=chunk_index,
                                content=chunk_text,
                                token_count=len(chunk_tokens),
                                page_number=page.page_number,
                                metadata={
                                    "page_number": page.page_number,
                                    "start_token": start,
                                    "end_token": end,
                                },
                            )
                        )

                        chunk_index += 1

                    if end >= len(token_ids):
                        break

                    start = end - self.chunk_overlap

        except Exception as exc:
            raise ChunkingError(
                "Failed to chunk document."
            ) from exc

        return chunks 

    