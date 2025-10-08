# Contract: Retriever Interface

**Component**: `src/retriever.py`
**Purpose**: Execute semantic search queries against vector store and return ranked results

---

## Interface

### `search(query_text: str, top_k: int = 5, similarity_threshold: float = 0.5) -> List[RetrievalResult]`

**Description**: Searches the vector store for chunks semantically similar to the query

**Input**:
- `query_text` (str): Natural language query from user
- `top_k` (int, optional): Maximum number of results (default: 5, fixed per requirements)
- `similarity_threshold` (float, optional): Minimum similarity score (default: 0.5, fixed per requirements)

**Output**:
- `List[RetrievalResult]`: Ranked results sorted by score (descending), filtered by threshold

**Preconditions**:
- Vector store is initialized and loaded
- `query_text` is not empty (length >= 3 characters)
- `top_k` > 0
- `similarity_threshold` in range [0.0, 1.0]
- At least one document has been ingested

**Postconditions**:
- Results are sorted by `similarity_score` descending
- All results have `similarity_score` >= `similarity_threshold`
- Number of results <= `top_k` (may be fewer if filtering removes results)
- Results may be empty list if no chunks meet threshold
- Each result includes complete chunk content and metadata

**Error Handling**:
- ValueError: Empty query_text or invalid parameters
- RuntimeError: Vector store not initialized
- RuntimeError: Embedder not available

---

## Contract Tests

### Test 1: Basic Query Returns Results
```python
def test_search_returns_relevant_results():
    # Given a retriever with ingested documents
    retriever = Retriever(embedder, vector_store)
    ingest_document("doc1.md", "# Python\nPython is a programming language.")

    # When searching for relevant content
    results = retriever.search("What is Python?", top_k=5)

    # Then relevant results are returned
    assert len(results) > 0
    assert all(isinstance(r, RetrievalResult) for r in results)
    assert all(r.similarity_score >= 0.5 for r in results)
    assert results[0].chunk.content  # Has content
```

### Test 2: Results Sorted by Score
```python
def test_search_results_sorted_by_score():
    # Given a retriever with multiple documents
    retriever = setup_retriever_with_docs()

    # When searching
    results = retriever.search("query", top_k=5)

    # Then results are sorted descending
    scores = [r.similarity_score for r in results]
    assert scores == sorted(scores, reverse=True)
```

### Test 3: Similarity Threshold Filtering
```python
def test_search_filters_by_threshold():
    # Given a retriever with mixed relevance documents
    retriever = setup_retriever()

    # When searching with threshold
    results = retriever.search("specific query", similarity_threshold=0.5)

    # Then only results above threshold returned
    assert all(r.similarity_score >= 0.5 for r in results)
```

### Test 4: Top-K Limit Respected
```python
def test_search_respects_top_k_limit():
    # Given a retriever with many documents
    retriever = setup_retriever_with_100_docs()

    # When searching with top_k=5
    results = retriever.search("query", top_k=5)

    # Then at most 5 results returned
    assert len(results) <= 5
```

### Test 5: Empty Results When No Matches
```python
def test_search_returns_empty_when_no_matches():
    # Given a retriever with documents about Python
    retriever = setup_retriever()
    ingest_document("python_doc.md", "Python programming content")

    # When searching for completely unrelated content
    results = retriever.search("quantum physics equations", similarity_threshold=0.5)

    # Then empty list returned (no results meet threshold)
    assert results == []
```

### Test 6: Result Includes Metadata
```python
def test_search_results_include_metadata():
    # Given a retriever with ingested doc
    retriever = setup_retriever()
    ingest_document("doc.md", "# Section\nContent here")

    # When searching
    results = retriever.search("content", top_k=5)

    # Then results include all metadata
    assert len(results) > 0
    result = results[0]
    assert result.chunk.metadata['source_file'] == "doc.md"
    assert result.chunk.metadata['header_path']
    assert result.rank >= 1
    assert 0.0 <= result.similarity_score <= 1.0
```

### Test 7: Error on Empty Query
```python
def test_search_rejects_empty_query():
    # Given a retriever
    retriever = setup_retriever()

    # When searching with empty query
    # Then raises ValueError
    with pytest.raises(ValueError, match="query_text cannot be empty"):
        retriever.search("")
```

### Test 8: Error When Not Initialized
```python
def test_search_fails_when_not_initialized():
    # Given an uninitialized retriever
    retriever = Retriever(embedder=None, vector_store=None)

    # When searching
    # Then raises RuntimeError
    with pytest.raises(RuntimeError, match="not initialized"):
        retriever.search("query")
```

### Test 9: Hybrid Retrieval (Dense + Sparse)
```python
def test_search_uses_hybrid_retrieval():
    # Given a retriever configured for hybrid search
    retriever = setup_hybrid_retriever()
    ingest_document("doc.md", "# FastAPI\nFastAPI is a web framework.")

    # When searching with specific term
    results = retriever.search("FastAPI", top_k=5)

    # Then results include score breakdown
    assert len(results) > 0
    result = results[0]
    assert 'dense_score' in result.score_breakdown
    assert 'sparse_score' in result.score_breakdown
    assert 'combined_score' in result.score_breakdown
```

### Test 10: Query Response Time
```python
def test_search_meets_performance_requirement():
    # Given a retriever with 1000 documents
    retriever = setup_retriever_with_1000_docs()

    # When searching
    import time
    start = time.perf_counter()
    results = retriever.search("test query", top_k=5)
    elapsed = time.perf_counter() - start

    # Then response time under 500ms
    assert elapsed < 0.5  # 500ms
    assert len(results) <= 5
```

---

## Integration Points

**Depends On**:
- `Embedder` - to encode query text
- `VectorStore` - to search for similar chunks
- `SparseRetriever` (optional) - for hybrid retrieval

**Used By**:
- `RAGEngine.query()` - for semantic search
- `RAGEngine.generate()` - to retrieve context for generation

---

**Status**: ✅ Contract Defined
**Implementation**: TDD - Write tests first, then implement
