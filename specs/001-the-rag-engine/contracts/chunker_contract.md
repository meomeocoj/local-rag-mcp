# Contract: Chunker Interface

**Component**: `src/chunker.py`
**Purpose**: Parse markdown files and split into logical chunks with metadata

---

## Interface

### `chunk_document(file_path: str, max_chunk_size: int = 500, overlap: int = 50) -> List[DocumentChunk]`

**Description**: Chunks a markdown file into semantically coherent segments

**Input**:
- `file_path` (str): Absolute path to .md file
- `max_chunk_size` (int, optional): Maximum tokens per chunk (default: 500)
- `overlap` (int, optional): Token overlap between chunks (default: 50)

**Output**:
- `List[DocumentChunk]`: Ordered list of chunks with metadata

**Preconditions**:
- File exists at `file_path`
- File has `.md` extension
- File is readable
- `max_chunk_size` > `overlap`
- `max_chunk_size` >= 50

**Postconditions**:
- Returns at least 1 chunk (even for small files)
- Chunks preserve markdown structure (code blocks intact)
- Header hierarchy captured in metadata
- Chunks ordered by position in document
- No chunk exceeds `max_chunk_size` (except single large code blocks)
- Adjacent chunks overlap by ~`overlap` tokens

**Error Handling**:
- FileNotFoundError: File doesn't exist
- ValueError: Invalid extension or unreadable file
- ValueError: Invalid chunk_size/overlap parameters

---

## Contract Tests

### Test 1: Basic Chunking
```python
def test_chunk_simple_markdown():
    # Given a markdown file with headers and content
    file_path = "test_doc.md"
    content = """
# Title
Some intro text.

## Section 1
Content for section 1 with multiple paragraphs.

## Section 2
Content for section 2.
"""
    write_file(file_path, content)

    # When chunking the document
    chunks = chunk_document(file_path, max_chunk_size=100)

    # Then chunks are created with metadata
    assert len(chunks) >= 1
    assert all(isinstance(c, DocumentChunk) for c in chunks)
    assert all(c.content for c in chunks)  # No empty chunks
    assert all(c.header_hierarchy is not None for c in chunks)
```

### Test 2: Code Block Preservation
```python
def test_chunk_preserves_code_blocks():
    # Given a markdown with code blocks
    content = """
## Example
Here's some code:
```python
def hello():
    print("world")
```
More text after.
"""
    file_path = write_temp_file(content)

    # When chunking
    chunks = chunk_document(file_path)

    # Then code blocks are kept intact
    code_chunks = [c for c in chunks if '```' in c.content]
    assert len(code_chunks) > 0
    for chunk in code_chunks:
        assert chunk.content.count('```') % 2 == 0  # Balanced fences
        assert chunk.metadata['contains_code'] is True
```

### Test 3: Header Hierarchy Tracking
```python
def test_chunk_tracks_header_hierarchy():
    # Given nested headers
    content = """
# Top Level
## Subsection
### Subsubsection
Content here.
"""
    file_path = write_temp_file(content)

    # When chunking
    chunks = chunk_document(file_path)

    # Then hierarchy is captured
    last_chunk = chunks[-1]
    assert last_chunk.header_hierarchy == ['Top Level', 'Subsection', 'Subsubsection']
```

### Test 4: Chunk Size Limits
```python
def test_chunk_respects_max_size():
    # Given a large document
    content = "# Header\n" + ("word " * 1000)  # Large content
    file_path = write_temp_file(content)

    # When chunking with size limit
    chunks = chunk_document(file_path, max_chunk_size=200)

    # Then chunks don't exceed limit (unless single atomic unit)
    for chunk in chunks:
        if not chunk.metadata.get('contains_code'):
            assert chunk.token_count <= 250  # Allow 25% tolerance
```

### Test 5: Overlap Between Chunks
```python
def test_chunks_have_overlap():
    # Given a document that produces multiple chunks
    content = "# Header\n" + (" ".join([f"word{i}" for i in range(500)]))
    file_path = write_temp_file(content)

    # When chunking with overlap
    chunks = chunk_document(file_path, max_chunk_size=100, overlap=20)

    # Then adjacent chunks share content
    if len(chunks) > 1:
        chunk1_words = set(chunks[0].content.split())
        chunk2_words = set(chunks[1].content.split())
        overlap = chunk1_words & chunk2_words
        assert len(overlap) > 0  # Some words shared
```

### Test 6: Error Handling - Missing File
```python
def test_chunk_missing_file_raises_error():
    # Given a non-existent file
    file_path = "/path/to/nonexistent.md"

    # When chunking
    # Then raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        chunk_document(file_path)
```

### Test 7: Error Handling - Invalid Extension
```python
def test_chunk_non_markdown_raises_error():
    # Given a non-markdown file
    file_path = "document.txt"
    write_file(file_path, "content")

    # When chunking
    # Then raises ValueError
    with pytest.raises(ValueError, match="must have .md extension"):
        chunk_document(file_path)
```

---

## Integration Points

**Depends On**:
- File system (read access)
- mistune library (markdown parsing)

**Used By**:
- `RAGEngine.ingest()` - during document ingestion
- Test suites for quality validation

---

**Status**: ✅ Contract Defined
**Implementation**: TDD - Write tests first, then implement
