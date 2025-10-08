# Contract: RAGEngine Interface

**Component**: `src/engine.py`
**Purpose**: Orchestrate document ingestion, querying, and deletion operations

---

## Interface

### `ingest(file_paths: List[str]) -> Dict[str, Any]`

**Description**: Batch ingest markdown documents into the vector store

**Input**:
- `file_paths` (List[str]): List of absolute paths to .md files

**Output**:
- Dict with keys:
  - `ingested_count` (int): Number of successfully ingested files
  - `failed_count` (int): Number of failed files
  - `chunk_count` (int): Total chunks created
  - `failed_files` (List[str]): Paths of files that failed

**Preconditions**:
- All paths in `file_paths` exist
- All files have .md extension
- `file_paths` is not empty

**Postconditions**:
- All valid files are chunked, embedded, and indexed
- Vector store persisted to disk
- Return dict contains accurate counts
- Partial success allowed (some files may fail)

**Error Handling**:
- ValueError: Empty file_paths list
- Individual file errors logged but don't halt batch

---

### `query(query_text: str) -> List[RetrievalResult]`

**Description**: Search for relevant document chunks

**Input**:
- `query_text` (str): Natural language query

**Output**:
- `List[RetrievalResult]`: Up to 5 results with score >= 0.5, sorted by relevance

**Preconditions**:
- Engine initialized with loaded vector store
- `query_text` not empty (>= 3 characters)
- At least one document ingested

**Postconditions**:
- Results meet functional requirements FR-011, FR-012, FR-013:
  - Response time < 500ms for up to 1000 docs
  - Returns up to 5 results
  - Filters results with score < 0.5
- Results sorted by score descending

**Error Handling**:
- ValueError: Empty or invalid query_text
- RuntimeError: Engine not initialized

---

### `delete(document_ids: List[str]) -> Dict[str, Any]`

**Description**: Manually remove documents from the index

**Input**:
- `document_ids` (List[str]): List of document IDs (file paths or hashes)

**Output**:
- Dict with keys:
  - `deleted_count` (int): Number of documents removed
  - `deleted_ids` (List[str]): IDs successfully deleted
  - `not_found_ids` (List[str]): IDs not in index

**Preconditions**:
- `document_ids` is not empty
- Engine initialized

**Postconditions**:
- All matching documents removed from vector store
- Vector store persisted
- Return dict contains accurate information

**Error Handling**:
- ValueError: Empty document_ids list
- Non-existent IDs logged in `not_found_ids`, no error raised

---

## Contract Tests

### Test 1: Ingest Single File
```python
def test_engine_ingest_single_file():
    # Given an engine and a markdown file
    engine = RAGEngine(config)
    file_path = create_test_file("test.md", "# Title\nContent")

    # When ingesting
    result = engine.ingest([file_path])

    # Then file is indexed
    assert result['ingested_count'] == 1
    assert result['failed_count'] == 0
    assert result['chunk_count'] > 0
    assert result['failed_files'] == []
```

### Test 2: Batch Ingest Multiple Files
```python
def test_engine_batch_ingest():
    # Given multiple markdown files
    engine = RAGEngine(config)
    files = [
        create_test_file("doc1.md", "# Doc 1\nContent 1"),
        create_test_file("doc2.md", "# Doc 2\nContent 2"),
        create_test_file("doc3.md", "# Doc 3\nContent 3"),
    ]

    # When batch ingesting
    result = engine.ingest(files)

    # Then all files indexed
    assert result['ingested_count'] == 3
    assert result['chunk_count'] >= 3
```

### Test 3: Ingest Handles Partial Failure
```python
def test_engine_ingest_partial_failure():
    # Given mix of valid and invalid files
    engine = RAGEngine(config)
    files = [
        create_test_file("valid.md", "# Valid\nContent"),
        "/nonexistent/file.md",
        create_test_file("also_valid.md", "# Also Valid\nContent"),
    ]

    # When batch ingesting
    result = engine.ingest(files)

    # Then valid files indexed, failure recorded
    assert result['ingested_count'] == 2
    assert result['failed_count'] == 1
    assert "/nonexistent/file.md" in result['failed_files']
```

### Test 4: Query Returns Results
```python
def test_engine_query_returns_results():
    # Given an engine with ingested content
    engine = RAGEngine(config)
    engine.ingest([create_test_file("doc.md", "# Python\nPython is great.")])

    # When querying
    results = engine.query("What is Python?")

    # Then relevant results returned
    assert len(results) > 0
    assert all(r.similarity_score >= 0.5 for r in results)
    assert "Python" in results[0].chunk.content
```

### Test 5: Query Respects Top-K and Threshold
```python
def test_engine_query_respects_constraints():
    # Given an engine with many documents
    engine = setup_engine_with_docs()

    # When querying
    results = engine.query("test query")

    # Then constraints enforced
    assert len(results) <= 5  # FR-012: max 5 results
    assert all(r.similarity_score >= 0.5 for r in results)  # FR-013: threshold
```

### Test 6: Query Performance Requirement
```python
def test_engine_query_performance():
    # Given an engine with 1000 documents
    engine = setup_engine_with_1000_docs()

    # When querying
    import time
    start = time.perf_counter()
    results = engine.query("test query")
    elapsed = time.perf_counter() - start

    # Then response under 500ms (FR-011)
    assert elapsed < 0.5
```

### Test 7: Delete Document
```python
def test_engine_delete_document():
    # Given an engine with ingested document
    engine = RAGEngine(config)
    file_path = create_test_file("doc.md", "# Content\nText")
    engine.ingest([file_path])

    # When deleting the document
    doc_id = hash_file_path(file_path)
    result = engine.delete([doc_id])

    # Then document removed
    assert result['deleted_count'] == 1
    assert doc_id in result['deleted_ids']
    assert result['not_found_ids'] == []

    # And query no longer finds it
    query_results = engine.query("Content")
    assert all(r.chunk.metadata['source_file'] != file_path for r in query_results)
```

### Test 8: Delete Handles Not Found
```python
def test_engine_delete_not_found():
    # Given an engine
    engine = RAGEngine(config)

    # When deleting non-existent document
    result = engine.delete(["nonexistent_id"])

    # Then gracefully handled
    assert result['deleted_count'] == 0
    assert "nonexistent_id" in result['not_found_ids']
```

### Test 9: Persistence Across Sessions
```python
def test_engine_persistence():
    # Given an engine with ingested data
    config = load_config()
    engine1 = RAGEngine(config)
    file_path = create_test_file("persist_test.md", "# Persistent\nData")
    engine1.ingest([file_path])

    # When creating new engine instance
    engine2 = RAGEngine(config)  # Loads from same persist directory

    # Then data is still available
    results = engine2.query("Persistent")
    assert len(results) > 0
    assert "Persistent" in results[0].chunk.content
```

### Test 10: Re-ingestion Updates Index
```python
def test_engine_reingest_updates():
    # Given an engine with ingested file
    engine = RAGEngine(config)
    file_path = create_test_file("doc.md", "# Original\nOriginal content")
    engine.ingest([file_path])

    # When file is modified and re-ingested
    update_file(file_path, "# Updated\nUpdated content")
    engine.ingest([file_path])

    # Then index reflects update (no duplicates)
    results = engine.query("Updated")
    assert len(results) > 0
    assert "Updated" in results[0].chunk.content

    # And old content not duplicated
    all_results = engine.query("content")
    source_files = [r.chunk.metadata['source_file'] for r in all_results]
    assert source_files.count(file_path) == len(set(chunk_ids_for(file_path)))  # No duplicates
```

---

## Integration Points

**Depends On**:
- `Chunker` - for document chunking
- `Embedder` - for generating embeddings
- `VectorStore` - for storage and retrieval
- `Retriever` - for query execution
- Config loader - for initialization

**Used By**:
- `main.py` CLI - user-facing commands
- Integration tests - end-to-end validation

---

**Status**: ✅ Contract Defined
**Implementation**: TDD - Write tests first, then implement
