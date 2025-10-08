# Contract: Chunker Interface

**Feature**: 002-use-langchain-markdownheadertextsplitter
**Date**: 2025-10-07
**Type**: Internal API Contract

## Overview

Defines the public interface contract for the `MarkdownChunker` class. This contract must remain stable to preserve compatibility with `engine.py` and other components.

---

## Class: MarkdownChunker

### Constructor

```python
def __init__(
    self,
    max_chunk_size: int = 1024,  # CHANGED from 512
    overlap: int = 100,            # CHANGED from 50
    strategy: str = "headers"      # UNCHANGED
) -> None
```

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_chunk_size` | int | No | 1024 | Maximum characters per chunk |
| `overlap` | int | No | 100 | Characters to overlap between chunks |
| `strategy` | str | No | "headers" | Chunking strategy ("headers" only post-refactor) |

**Constraints**:
- `max_chunk_size` > 0
- `overlap` >= 0
- `overlap` < `max_chunk_size`
- `strategy` must be "headers" (other strategies removed in this refactor)

**Changes from Current**:
- Default `max_chunk_size`: 512 → 1024
- Default `overlap`: 50 → 100
- Removed strategies: "paragraphs", "semantic", "recursive" (per FR-007)

---

### Method: chunk_document

```python
def chunk_document(
    self,
    text: str,
    source: str = None
) -> List[Chunk]
```

**Purpose**: Chunk a markdown document while preserving header hierarchy.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | str | Yes | - | Markdown document content |
| `source` | str | No | None | Source identifier (filename/path) |

**Returns**: `List[Chunk]`

**Return Type**:
```python
List[Chunk]  # where Chunk is a dataclass with:
             # - text: str
             # - metadata: Dict[str, Any]
```

**Behavior**:
1. Parse markdown text using LangChain MarkdownHeaderTextSplitter
2. Extract header hierarchy for each chunk
3. Apply chunk size constraints (1024 chars max, 100 char overlap)
4. Return list of Chunk objects with metadata

**Invariants (Post-conditions)**:
- All returned chunks have `len(chunk.text) <= max_chunk_size`
- All chunks have `metadata["headers"]` field (may be empty list for headerless docs)
- All chunks have `metadata["position"]` field (0-indexed)
- All chunks have `metadata["source"]` field (equals `source` parameter or empty string)
- Chunks are ordered by position (index 0 is first chunk in document)

**Error Handling**:
- Empty `text`: Returns empty list `[]`
- Invalid markdown: Gracefully degrades to character-based splitting
- Text without headers: Returns single chunk (if ≤1024 chars) or character-split chunks

**Changes from Current**:
- ✅ Signature unchanged (preserves compatibility)
- **MODIFIED**: Internal implementation uses LangChain instead of custom mistune logic
- **MODIFIED**: Metadata structure enhanced (header dicts vs simple strings)

---

## Data Class: Chunk

### Structure

```python
@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any]
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | str | Yes | The chunk content |
| `metadata` | Dict[str, Any] | Yes | Associated metadata |

**Metadata Structure**:
```python
{
    "headers": List[Dict[str, Union[int, str]]],  # MODIFIED structure
    "position": int,                               # UNCHANGED
    "source": str,                                 # UNCHANGED
    "recursive_chunk": bool (optional)             # NEW (optional)
}
```

**Metadata Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `headers` | List[Dict] | Yes | Header hierarchy | See HeaderInfo contract |
| `position` | int | Yes | Chunk index in source | position >= 0 |
| `source` | str | Yes | Source identifier | Non-empty string |
| `recursive_chunk` | bool | No | True if split beyond headers | Default: False |

**HeaderInfo Structure** (within `metadata["headers"]`):
```python
{
    "level": int,  # 1-6 for H1-H6
    "text": str    # Header content
}
```

**Changes from Current**:
- ✅ `Chunk` dataclass interface unchanged
- **MODIFIED**: `metadata["headers"]` structure (was `List[Dict]` as strings, now proper dict structure)
- **NEW**: `metadata["recursive_chunk"]` optional field

---

## Contract Tests

### Test: Constructor Defaults

```python
def test_chunker_constructor_defaults():
    """Verify default parameters match spec."""
    chunker = MarkdownChunker()
    assert chunker.max_chunk_size == 1024
    assert chunker.overlap == 100
    assert chunker.strategy == "headers"
```

### Test: Chunk Interface

```python
def test_chunk_dataclass_structure():
    """Verify Chunk has required fields."""
    chunk = Chunk(
        text="test content",
        metadata={"headers": [], "position": 0, "source": "test.md"}
    )
    assert hasattr(chunk, 'text')
    assert hasattr(chunk, 'metadata')
    assert isinstance(chunk.text, str)
    assert isinstance(chunk.metadata, dict)
```

### Test: Metadata Structure

```python
def test_chunk_metadata_required_fields():
    """Verify all chunks have required metadata fields."""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document("# Test\nContent", source="test.md")

    for chunk in chunks:
        assert "headers" in chunk.metadata
        assert "position" in chunk.metadata
        assert "source" in chunk.metadata
        assert isinstance(chunk.metadata["headers"], list)
        assert isinstance(chunk.metadata["position"], int)
        assert isinstance(chunk.metadata["source"], str)
```

### Test: Header Hierarchy Structure

```python
def test_header_metadata_structure():
    """Verify header objects have correct structure."""
    chunker = MarkdownChunker()
    md = "# Title\n## Section\nContent"
    chunks = chunker.chunk_document(md, source="test.md")

    for chunk in chunks:
        for header in chunk.metadata["headers"]:
            assert "level" in header
            assert "text" in header
            assert isinstance(header["level"], int)
            assert isinstance(header["text"], str)
            assert 1 <= header["level"] <= 6
```

### Test: Chunk Size Constraint

```python
def test_chunk_size_constraint():
    """Verify no chunk exceeds max_chunk_size."""
    chunker = MarkdownChunker(max_chunk_size=1024)
    # Create large document
    large_md = "# Title\n" + ("A" * 5000)
    chunks = chunker.chunk_document(large_md, source="large.md")

    for chunk in chunks:
        assert len(chunk.text) <= 1024
```

### Test: Position Ordering

```python
def test_chunk_position_ordering():
    """Verify chunks are ordered by position."""
    chunker = MarkdownChunker()
    md = "# A\nContent A\n## B\nContent B\n### C\nContent C"
    chunks = chunker.chunk_document(md, source="test.md")

    positions = [c.metadata["position"] for c in chunks]
    assert positions == sorted(positions)
    assert positions[0] == 0
```

### Test: Source Propagation

```python
def test_source_metadata_propagation():
    """Verify source parameter flows to all chunks."""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document("# Test\nContent", source="my-doc.md")

    for chunk in chunks:
        assert chunk.metadata["source"] == "my-doc.md"
```

### Test: Headerless Document Handling

```python
def test_headerless_document_handling():
    """Verify headerless docs return single chunk if small."""
    chunker = MarkdownChunker(max_chunk_size=1024)
    small_text = "Just plain text without headers." * 10  # ~320 chars
    chunks = chunker.chunk_document(small_text, source="plain.md")

    assert len(chunks) == 1  # Single chunk
    assert chunks[0].metadata["headers"] == []  # No headers
    assert len(chunks[0].text) <= 1024
```

### Test: Empty Input

```python
def test_empty_input_returns_empty_list():
    """Verify empty text returns empty list."""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document("", source="empty.md")
    assert chunks == []
```

---

## Backward Compatibility

### Breaking Changes
- **Constructor defaults**: `max_chunk_size` and `overlap` changed (config-level, not code-level breaking)
- **Metadata structure**: `headers` field structure modified (requires vector store re-indexing)
- **Removed strategies**: "paragraphs", "semantic", "recursive" strategies removed

### Non-Breaking Changes
- ✅ `chunk_document()` signature unchanged
- ✅ `Chunk` dataclass interface unchanged
- ✅ Return type `List[Chunk]` unchanged

### Migration Path
1. Update `config.yaml` with new defaults (automated)
2. Clear vector store: `main.py clear --confirm`
3. Re-ingest documents: `main.py ingest data/documents/*.md`

---

## Acceptance Criteria

1. ✅ All existing `engine.py` calls to `chunker.chunk_document()` work without modification
2. ✅ All contract tests pass (RED state initially, GREEN after implementation)
3. ✅ Metadata includes header hierarchy in new format
4. ✅ Chunk size constraint (≤1024 chars) enforced
5. ✅ Position and source metadata preserved

---

**Status**: Contract defined. Tests ready for TDD RED phase.
