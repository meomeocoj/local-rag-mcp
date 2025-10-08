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


def test_token_limit_enforcement():
    """Test that chunks never exceed max token limit."""
    # Use conservative token limit
    max_tokens = 1000
    chunker = MarkdownChunker(max_chunk_size=10000, overlap=50, max_tokens_per_chunk=max_tokens)

    # Create extremely large content (way over token limit)
    huge_paragraph = "This is a sentence with many words. " * 500  # ~3500 words = ~4600 tokens

    markdown_text = f"""# Huge Section

{huge_paragraph}

## Another Section

{huge_paragraph}
"""

    chunks = chunker.chunk_document(markdown_text, source="huge.md")

    # All chunks must respect token limit (1 token ≈ 4 chars)
    max_chars = max_tokens * 4
    for chunk in chunks:
        estimated_tokens = len(chunk.text) // 4
        assert estimated_tokens <= max_tokens, f"Chunk has ~{estimated_tokens} tokens, exceeds limit of {max_tokens}"
        assert len(chunk.text) <= max_chars + 100  # Small tolerance for splitting


def test_embedding_api_batch_safety():
    """Test that chunks are safe for embedding API with 5461 token limit."""
    # Simulate real-world scenario with embedding API limit
    max_tokens = 5000  # Conservative limit under 5461
    chunker = MarkdownChunker(max_chunk_size=20000, overlap=100, max_tokens_per_chunk=max_tokens)

    # Create content that would exceed API limit if not split
    large_section = "Word " * 10000  # ~10000 tokens

    markdown_text = f"""# Large Documentation

{large_section}
"""

    chunks = chunker.chunk_document(markdown_text, source="api_test.md")

    # Verify no single chunk exceeds safe limit
    for chunk in chunks:
        estimated_tokens = len(chunk.text) // 4
        assert estimated_tokens <= max_tokens, f"Chunk would exceed API limit: ~{estimated_tokens} tokens"


# Deprecated tests removed - these tested the old "paragraphs" strategy
# which was removed in favor of LangChain MarkdownHeaderTextSplitter
# See specs/002-use-langchain-markdownheadertextsplitter/ for migration details
