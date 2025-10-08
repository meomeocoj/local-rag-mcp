# Data Model: LangChain MarkdownHeaderTextSplitter Integration

**Feature**: 002-use-langchain-markdownheadertextsplitter
**Date**: 2025-10-07

## Overview

This document defines the data structures and their relationships for the LangChain MarkdownHeaderTextSplitter integration. Since this is primarily a refactor of the chunking layer, most entities remain unchanged. The focus is on the `Chunk` entity and its metadata structure.

---

## Core Entities

### 1. Chunk

**Purpose**: Represents a segment of text extracted from a markdown document with hierarchical context.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `text` | str | Yes | The actual chunk content | 1 ≤ len ≤ 1024 chars |
| `metadata` | dict | Yes | Associated metadata | See Chunk Metadata structure |

**Behavior**:
- Immutable after creation
- Preserves header hierarchy from source document
- Maintains position information for ordering

**Changes from Current**:
- ✅ Interface unchanged (preserves compatibility with `engine.py`)
- ✅ Metadata structure enhanced (richer header information)

**Example**:
```python
Chunk(
    text="## Database\n\nConfigure connection pooling for optimal performance...",
    metadata={
        "headers": [
            {"level": 1, "text": "Configuration"},
            {"level": 2, "text": "Database"}
        ],
        "position": 3,
        "source": "setup-guide.md"
    }
)
```

---

### 2. Chunk Metadata

**Purpose**: Contextual information attached to each chunk for retrieval and display.

**Structure**:
```python
{
    "headers": List[HeaderInfo],      # Header hierarchy (NEW: enhanced structure)
    "position": int,                   # Chunk order in source document
    "source": str,                     # Source document filename/path
    "recursive_chunk": bool (optional) # Flag if chunk was split beyond header boundaries
}
```

**Attributes**:
| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `headers` | List[HeaderInfo] | Yes | Ordered list of parent headers | 0-6 elements (H1-H6) |
| `position` | int | Yes | Zero-based chunk index in source | position ≥ 0 |
| `source` | str | Yes | Source document identifier | Non-empty string |
| `recursive_chunk` | bool | No | True if chunk exceeded 1024 chars and was split | Default: False |

**Changes from Current**:
- **MODIFIED**: `headers` field structure (was simple list of strings, now list of dict with level + text)
- ✅ `position` and `source` unchanged
- **NEW**: `recursive_chunk` flag for diagnostics

---

### 3. HeaderInfo

**Purpose**: Represents a single header in the document hierarchy.

**Structure**:
```python
{
    "level": int,     # Header depth (1-6 for H1-H6)
    "text": str       # Header content
}
```

**Attributes**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `level` | int | Yes | Header depth | 1 ≤ level ≤ 6 |
| `text` | str | Yes | Header text content | Non-empty, max 200 chars |

**Invariants**:
- Headers in `Chunk.metadata["headers"]` must be in ascending order by position (parent before child)
- Level sequence must be valid (can't jump from H1 to H3 without H2)

**Example**:
```python
[
    {"level": 1, "text": "API Reference"},
    {"level": 2, "text": "Authentication"},
    {"level": 3, "text": "OAuth 2.0"}
]
```

---

## Entity Relationships

```
Document (markdown file)
    │
    ├──> splits_into ──> [Chunk, Chunk, ...]
    │
    └──> Chunk
            ├── text: str
            └── metadata
                    ├── headers: [HeaderInfo, ...]
                    ├── position: int
                    ├── source: str
                    └── recursive_chunk: bool (optional)

HeaderInfo
    ├── level: int (1-6)
    └── text: str
```

**Cardinality**:
- 1 Document → 1 to N Chunks (N depends on document size and header structure)
- 1 Chunk → 0 to 6 HeaderInfo objects (maximum header depth H1-H6)
- HeaderInfo objects are ordered by document structure (parent before child)

---

## State Transitions

### Chunk Lifecycle

```
┌─────────────┐
│  Markdown   │
│  Document   │
└──────┬──────┘
       │
       │ MarkdownHeaderTextSplitter.split_text()
       ▼
┌─────────────┐
│  Raw Chunks │  (LangChain Document objects)
│  (temp)     │
└──────┬──────┘
       │
       │ _convert_to_chunk()
       ▼
┌─────────────┐
│   Chunk     │  (Immutable)
│  (Created)  │
└──────┬──────┘
       │
       │ embedder.embed()
       ▼
┌─────────────┐
│  Embedding  │
│  (Vector)   │
└──────┬──────┘
       │
       │ vector_store.add()
       ▼
┌─────────────┐
│  Persisted  │  (ChromaDB)
│   Chunk     │
└─────────────┘
```

**States**:
1. **Raw**: Freshly split by LangChain (transient)
2. **Created**: Converted to internal `Chunk` format (immutable)
3. **Embedded**: Vector representation generated (immutable)
4. **Persisted**: Stored in ChromaDB with metadata (immutable)

**No State Mutations**: Chunks are immutable once created. Updates require delete + re-create.

---

## Data Validation Rules

### Chunk Validation
```python
def validate_chunk(chunk: Chunk) -> bool:
    """Validate chunk meets requirements."""
    # Text constraints
    assert 1 <= len(chunk.text) <= 1024, "Chunk text must be 1-1024 chars"

    # Metadata presence
    assert chunk.metadata is not None, "Metadata required"
    assert "headers" in chunk.metadata, "Headers field required"
    assert "position" in chunk.metadata, "Position field required"
    assert "source" in chunk.metadata, "Source field required"

    # Position constraints
    assert chunk.metadata["position"] >= 0, "Position must be non-negative"

    # Source constraints
    assert len(chunk.metadata["source"]) > 0, "Source must be non-empty"

    # Headers validation
    headers = chunk.metadata["headers"]
    assert isinstance(headers, list), "Headers must be a list"
    assert len(headers) <= 6, "Max 6 header levels"

    for header in headers:
        assert "level" in header, "Header must have level"
        assert "text" in header, "Header must have text"
        assert 1 <= header["level"] <= 6, "Header level must be 1-6"
        assert len(header["text"]) > 0, "Header text must be non-empty"
        assert len(header["text"]) <= 200, "Header text max 200 chars"

    # Header ordering
    if len(headers) > 1:
        for i in range(len(headers) - 1):
            assert headers[i]["level"] <= headers[i+1]["level"], \
                "Headers must be in ascending order"

    return True
```

### HeaderInfo Validation
```python
def validate_header_info(header: dict) -> bool:
    """Validate header info structure."""
    assert "level" in header, "Missing level"
    assert "text" in header, "Missing text"
    assert isinstance(header["level"], int), "Level must be int"
    assert isinstance(header["text"], str), "Text must be str"
    assert 1 <= header["level"] <= 6, "Invalid level"
    assert 0 < len(header["text"]) <= 200, "Invalid text length"
    return True
```

---

## Serialization & Storage

### JSON Serialization (Vector Store Metadata)

**Format**:
```json
{
    "headers": "[{\"level\": 1, \"text\": \"Config\"}, {\"level\": 2, \"text\": \"Database\"}]",
    "position": 3,
    "source": "setup.md",
    "recursive_chunk": "false"
}
```

**Rationale**:
- ChromaDB requires flat string values for complex metadata
- Use `json.dumps()` for serialization (already implemented in `vector_store.py`)
- Use `json.loads()` for deserialization on retrieval

**Serialization Logic** (existing in `vector_store.py`):
```python
# Serialize
sanitized = {}
for key, value in metadata.items():
    if isinstance(value, (list, dict)):
        sanitized[key] = json.dumps(value)  # Existing behavior
    else:
        sanitized[key] = value
```

**Deserialization Logic** (existing in `vector_store.py`):
```python
# Deserialize
deserialized = {}
for key, value in metadata.items():
    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
        try:
            deserialized[key] = json.loads(value)  # Existing behavior
        except json.JSONDecodeError:
            deserialized[key] = value
    else:
        deserialized[key] = value
```

---

## Migration Considerations

### Data Compatibility

**Old Format** (pre-langchain):
```python
{
    "headers": "[{'level': 3, 'text': 'Tables'}, {'level': 4, 'text': 'Snapshots'}]",  # String
    "position": 12,
    "source": "ducklake.txt"
}
```

**New Format** (post-langchain):
```python
{
    "headers": "[{\"level\": 1, \"text\": \"Configuration\"}, {\"level\": 2, \"text\": \"Database\"}]",  # String (JSON)
    "position": 3,
    "source": "config.md",
    "recursive_chunk": "false"  # New field
}
```

**Compatibility**:
- ✅ Both use JSON serialization for headers (compatible)
- ✅ `position` and `source` unchanged
- ✅ New `recursive_chunk` field is optional (backward compatible for reads)
- ⚠️ Old chunks remain in DB after upgrade but won't have new chunking behavior
- ✅ Manual re-ingestion required (per FR-005) to use new chunker

---

## Example Data Flow

### Document Ingestion

**Input Document** (`config.md`):
```markdown
# Configuration

This guide covers configuration options.

## Database

Configure your database connection.

### Connection Pooling

Set pool size and timeout values.
```

**Output Chunks**:
```python
[
    Chunk(
        text="# Configuration\n\nThis guide covers configuration options.",
        metadata={
            "headers": [{"level": 1, "text": "Configuration"}],
            "position": 0,
            "source": "config.md"
        }
    ),
    Chunk(
        text="## Database\n\nConfigure your database connection.",
        metadata={
            "headers": [
                {"level": 1, "text": "Configuration"},
                {"level": 2, "text": "Database"}
            ],
            "position": 1,
            "source": "config.md"
        }
    ),
    Chunk(
        text="### Connection Pooling\n\nSet pool size and timeout values.",
        metadata={
            "headers": [
                {"level": 1, "text": "Configuration"},
                {"level": 2, "text": "Database"},
                {"level": 3, "text": "Connection Pooling"}
            ],
            "position": 2,
            "source": "config.md"
        }
    )
]
```

---

## Testing Strategy

### Contract Tests
```python
def test_chunk_interface_unchanged():
    """Verify Chunk dataclass interface."""
    chunk = Chunk(text="test", metadata={})
    assert hasattr(chunk, 'text')
    assert hasattr(chunk, 'metadata')

def test_metadata_structure():
    """Verify metadata contains required fields."""
    metadata = {
        "headers": [{"level": 1, "text": "Test"}],
        "position": 0,
        "source": "test.md"
    }
    assert "headers" in metadata
    assert isinstance(metadata["headers"], list)
    assert all("level" in h and "text" in h for h in metadata["headers"])
```

### Unit Tests
```python
def test_header_hierarchy_preserved():
    """Verify header context flows through."""
    # Test H1 → H2 → H3 structure preserved in metadata

def test_chunk_size_constraint():
    """Verify chunks don't exceed 1024 chars."""
    # Test with large documents

def test_headerless_document_handling():
    """Verify fallback for docs without headers."""
    # Test single chunk for small headerless doc
    # Test character split for large headerless doc
```

---

**Status**: ✅ Data model complete. Ready for contracts generation.
