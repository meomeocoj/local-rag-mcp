"""Contract tests for MarkdownChunker with LangChain integration."""

import pytest
from src.chunker import MarkdownChunker, Chunk


# ===== Contract Tests (T004-T012) =====

def test_chunker_constructor_defaults():
    """T004: Verify default parameters match new spec."""
    chunker = MarkdownChunker()
    assert chunker.max_chunk_size == 1024, "Default max_chunk_size should be 1024"
    assert chunker.overlap == 100, "Default overlap should be 100"
    assert chunker.strategy == "headers", "Default strategy should be headers"


def test_chunk_dataclass_structure():
    """T005: Verify Chunk has required fields."""
    chunk = Chunk(
        text="test content",
        metadata={"headers": [], "position": 0, "source": "test.md"}
    )
    assert hasattr(chunk, 'text'), "Chunk must have text attribute"
    assert hasattr(chunk, 'metadata'), "Chunk must have metadata attribute"
    assert isinstance(chunk.text, str), "Text must be string"
    assert isinstance(chunk.metadata, dict), "Metadata must be dict"


def test_chunk_metadata_required_fields():
    """T006: Verify all chunks have required metadata fields."""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document("# Test\nContent", source="test.md")

    assert len(chunks) > 0, "Should produce at least one chunk"
    for chunk in chunks:
        assert "headers" in chunk.metadata, "Chunk must have headers field"
        assert "position" in chunk.metadata, "Chunk must have position field"
        assert "source" in chunk.metadata, "Chunk must have source field"
        assert isinstance(chunk.metadata["headers"], list), "Headers must be list"
        assert isinstance(chunk.metadata["position"], int), "Position must be int"
        assert isinstance(chunk.metadata["source"], str), "Source must be str"


def test_header_metadata_structure():
    """T007: Verify header objects have correct structure."""
    chunker = MarkdownChunker()
    md = "# Title\n## Section\nContent"
    chunks = chunker.chunk_document(md, source="test.md")

    assert len(chunks) > 0, "Should produce chunks"
    for chunk in chunks:
        for header in chunk.metadata["headers"]:
            assert "level" in header, "Header must have level field"
            assert "text" in header, "Header must have text field"
            assert isinstance(header["level"], int), "Level must be int"
            assert isinstance(header["text"], str), "Text must be str"
            assert 1 <= header["level"] <= 6, f"Level must be 1-6, got {header['level']}"


def test_chunk_size_constraint():
    """T008: Verify no chunk exceeds max_chunk_size."""
    chunker = MarkdownChunker(max_chunk_size=1024)
    # Create large document that should be split
    large_md = "# Title\n" + ("A" * 5000)
    chunks = chunker.chunk_document(large_md, source="large.md")

    assert len(chunks) > 0, "Should produce chunks"
    for chunk in chunks:
        assert len(chunk.text) <= 1024, f"Chunk size {len(chunk.text)} exceeds 1024"


def test_chunk_position_ordering():
    """T009: Verify chunks are ordered by position."""
    chunker = MarkdownChunker()
    md = "# A\nContent A\n## B\nContent B\n### C\nContent C"
    chunks = chunker.chunk_document(md, source="test.md")

    assert len(chunks) > 0, "Should produce chunks"
    positions = [c.metadata["position"] for c in chunks]
    assert positions == sorted(positions), "Positions should be in ascending order"
    assert positions[0] == 0, "First position should be 0"


def test_source_metadata_propagation():
    """T010: Verify source parameter flows to all chunks."""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document("# Test\nContent", source="my-doc.md")

    assert len(chunks) > 0, "Should produce chunks"
    for chunk in chunks:
        assert chunk.metadata["source"] == "my-doc.md", "Source should be my-doc.md"


def test_headerless_document_handling():
    """T011: Verify headerless docs return single chunk if small."""
    chunker = MarkdownChunker(max_chunk_size=1024)
    small_text = "Just plain text without headers." * 10  # ~320 chars
    chunks = chunker.chunk_document(small_text, source="plain.md")

    assert len(chunks) >= 1, "Should produce at least one chunk"
    # Headerless document should have empty headers list
    assert chunks[0].metadata["headers"] == [], "Headerless doc should have empty headers"
    assert len(chunks[0].text) <= 1024, "Chunk should not exceed max size"


def test_empty_input_returns_empty_list():
    """T012: Verify empty text returns empty list."""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document("", source="empty.md")
    assert chunks == [], "Empty input should return empty list"
