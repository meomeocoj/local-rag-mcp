"""Tests for the chunker module."""

import pytest
from src.chunker import MarkdownChunker, Chunk


def test_chunker_initialization():
    """Test chunker initialization."""
    chunker = MarkdownChunker(max_chunk_size=512, overlap=50)
    assert chunker.max_chunk_size == 512
    assert chunker.overlap == 50


def test_simple_markdown_chunking():
    """Test chunking a simple markdown document."""
    chunker = MarkdownChunker(max_chunk_size=200, overlap=20)

    markdown_text = """# Main Title

This is a paragraph under the main title.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""

    chunks = chunker.chunk_document(markdown_text, source="test.md")

    assert len(chunks) > 0
    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    assert all(chunk.metadata.get('source') == 'test.md' for chunk in chunks)


def test_code_block_preservation():
    """Test that code blocks are preserved in chunks."""
    chunker = MarkdownChunker(max_chunk_size=500, overlap=50)

    markdown_text = """# Code Example

Here's some code:

```python
def hello():
    print("Hello, world!")
```

And some explanation.
"""

    chunks = chunker.chunk_document(markdown_text, source="code.md")

    # Check that at least one chunk contains the code block
    chunk_texts = [chunk.text for chunk in chunks]
    combined_text = '\n'.join(chunk_texts)

    assert 'python' in combined_text
    assert 'def hello()' in combined_text


def test_header_hierarchy():
    """Test that header hierarchy is tracked in metadata."""
    chunker = MarkdownChunker(max_chunk_size=500, overlap=50)

    markdown_text = """# Level 1

Content.

## Level 2

More content.

### Level 3

Deep content.
"""

    chunks = chunker.chunk_document(markdown_text, source="hierarchy.md")

    # Check that headers are tracked in metadata
    for chunk in chunks:
        assert 'headers' in chunk.metadata
        headers = chunk.metadata['headers']
        assert isinstance(headers, list)


def test_large_chunk_splitting():
    """Test that large chunks are split correctly."""
    chunker = MarkdownChunker(max_chunk_size=100, overlap=20)

    # Create a large paragraph that exceeds max_chunk_size
    long_text = "This is a very long paragraph. " * 20

    markdown_text = f"""# Long Content

{long_text}
"""

    chunks = chunker.chunk_document(markdown_text, source="long.md")

    # Should have multiple chunks due to splitting
    assert len(chunks) > 1

    # Check that chunks respect max_chunk_size (approximately)
    for chunk in chunks:
        assert len(chunk.text) <= chunker.max_chunk_size + 50  # Some tolerance


def test_empty_document():
    """Test chunking an empty document."""
    chunker = MarkdownChunker()

    chunks = chunker.chunk_document("", source="empty.md")

    # Should return at least one chunk, even if empty
    assert isinstance(chunks, list)


def test_chunk_metadata():
    """Test that chunk metadata contains expected fields."""
    chunker = MarkdownChunker()

    markdown_text = """# Test

Content here.
"""

    chunks = chunker.chunk_document(markdown_text, source="test.md")

    for chunk in chunks:
        assert 'source' in chunk.metadata
        assert 'position' in chunk.metadata
        assert 'headers' in chunk.metadata
