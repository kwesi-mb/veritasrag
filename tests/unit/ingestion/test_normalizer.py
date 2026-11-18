from app.ingestion.normalizer import TextNormalizer


def test_normalize_removes_excessive_whitespace():
    text = "Hello      world\n\n\n\nThis is VeritasRAG."

    result = TextNormalizer.normalize(text)

    assert result == "Hello world\n\nThis is VeritasRAG."

def test_normalize_preserves_paragraphs():
    text = "First paragraph.\n\nSecond paragraph."

    result = TextNormalizer.normalize(text)

    assert result == text


def test_normalize_handles_empty_text():
    assert TextNormalizer.normalize("") == ""

def test_normalize_handles_unicode():
    text = "AI   Engineering"

    result = TextNormalizer.normalize(text)

    assert result == "AI Engineering"

def test_normalize_removes_null_characters():
    text = "Hello\x00World"

    result = TextNormalizer.normalize(text)

    assert result == "HelloWorld"