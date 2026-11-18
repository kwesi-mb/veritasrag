from app.ingestion.chunker import DocumentChunker
from app.ingestion.parsers import ParsedPage


class FakeTokenizer:

    def encode(self, text: str) -> list[int]:
        return [
            int(token)
            for token in text.split()
        ]

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(
            str(token)
            for token in token_ids
        )

    def special_token_count(self) -> int:
        return 2

def test_chunker_creates_chunks():
    tokenizer = FakeTokenizer()

    chunker = DocumentChunker(
        tokenizer=tokenizer,
        chunk_size=8,
        chunk_overlap=2,
    )

    pages = [
        ParsedPage(
            page_number=1,
            content="1 2 3 4 5 6 7 8 9 10",
        )
    ]

    chunks = chunker.chunk_pages(pages)

    assert len(chunks) == 2

    assert chunks[0].content == "1 2 3 4 5 6"
    assert chunks[1].content == "5 6 7 8 9 10"

    assert chunks[0].token_count == 6
    assert chunks[1].token_count == 6


def test_chunker_pressure_page_numbers():
    tokenizer = FakeTokenizer()

    chunker = DocumentChunker(
        tokenizer=tokenizer,
        chunk_size=8,
        chunk_overlap=2,
    )

    pages = [
        ParsedPage(1, "1 2 3 4 5 6"),
        ParsedPage(2, "7 8 9 10 11 12"),
    ]


    chunks = chunker.chunk_pages(pages)

    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2

    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1

def test_chunker_skips_empty_pages():
    chunker = DocumentChunker(
        tokenizer=FakeTokenizer(),
    )

    pages = [
        ParsedPage(1, ""),
        ParsedPage(2, "1 2 3"),
    ]

    chunks = chunker.chunk_pages(pages)

    assert len(chunks) == 1
    assert chunks[0].page_number == 2

def test_chunker_rejects_invalid_overlap():
    import pytest

    with pytest.raises(ValueError):
        DocumentChunker(
            tokenizer=FakeTokenizer(),
            chunk_size=8,
            chunk_overlap=6,
        )