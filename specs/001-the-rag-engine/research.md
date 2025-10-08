# Research: Optimized RAG Engine for Local Markdown Documents

**Date**: 2025-10-06
**Feature**: 001-the-rag-engine

## Research Areas

### 1. Performance Optimization for <500ms Query Response

**Decision**: Use hybrid retrieval (dense + sparse) with pre-computed embeddings

**Rationale**:
- Dense retrieval (sentence-transformers) provides semantic understanding
- Sparse retrieval (BM25) provides lexical matching for technical terms/code
- ChromaDB supports efficient vector search with HNSW indexing
- Pre-computing and persisting embeddings eliminates re-computation overhead
- Existing codebase already has both dense and sparse retrieval implementations

**Alternatives Considered**:
- Pure dense retrieval: May miss exact keyword matches in technical docs
- Pure sparse retrieval: Lacks semantic understanding for natural language queries
- Re-ranking with cross-encoders: Adds latency, deferred as future enhancement

**Implementation Notes**:
- Keep vector store warm (persistent ChromaDB connection)
- Use batch embedding for ingestion efficiency
- Leverage existing sparse_retriever.py for BM25

### 2. Intelligent Markdown Chunking at Logical Boundaries

**Decision**: Header-based hierarchical chunking with context preservation

**Rationale**:
- Markdown structure (H1, H2, H3) provides natural semantic boundaries
- Preserves document hierarchy for context
- Code blocks kept intact to maintain syntactic correctness
- Existing chunker.py already implements this approach using mistune

**Alternatives Considered**:
- Fixed-size chunking: Breaks semantic units and code blocks
- Sentence-based chunking: Too granular, loses context
- Recursive chunking: Added complexity without clear benefit for markdown

**Implementation Notes**:
- Current chunker tracks header hierarchy in metadata
- Chunk size configurable via config.yaml
- Overlap between chunks maintains context continuity

### 3. Similarity Score Filtering (0.5 Threshold)

**Decision**: Apply post-retrieval filtering with configurable threshold

**Rationale**:
- Prevents irrelevant results from polluting output
- 0.5 threshold balances precision vs recall for documentation retrieval
- Better user experience than showing weakly related content
- Allows returning <5 results when no good matches exist

**Alternatives Considered**:
- No filtering: Users must manually assess relevance
- Higher threshold (0.7): May filter out useful but not perfect matches
- Dynamic threshold: Adds complexity without clear user value

**Implementation Notes**:
- Filter after retrieval but before returning to user
- Log filtered results for quality monitoring
- Threshold configurable in config.yaml for tuning

### 4. Batch Ingestion Strategy

**Decision**: Accept multiple file paths in single command with batch embedding

**Rationale**:
- Sentence-transformers supports efficient batch encoding
- Amortizes embedding model load time across multiple files
- Single ChromaDB transaction for atomicity
- Simpler UX than directory recursion

**Alternatives Considered**:
- Directory traversal: Requires glob patterns, unclear inclusion rules
- One-at-a-time ingestion: Slower due to repeated model loading
- Async ingestion: Complexity not justified for local operation

**Implementation Notes**:
- CLI accepts space-separated file paths
- Validate all files exist before starting ingestion
- Use batch_size parameter for embedder to optimize memory

### 5. Manual Document Deletion Approach

**Decision**: Explicit delete command, no auto-sync with file system

**Rationale**:
- User maintains control over index contents
- Simpler implementation (no file watching or polling)
- Avoids accidental deletions from temporary file moves
- Consistent with "explicit is better than implicit" principle

**Alternatives Considered**:
- Auto-detect on query: Adds latency, partial failures confusing
- Periodic sync command: When to run? Risk of surprise deletions
- File watcher: Complexity, platform-specific behavior

**Implementation Notes**:
- Delete by document ID or file path
- Batch delete support for multiple documents
- Return list of deleted IDs for confirmation

## Technology Stack Validation

### Current Dependencies (Validated)

| Dependency | Version | Purpose | Status |
|------------|---------|---------|--------|
| mistune | >=3.0.0 | Markdown parsing | ✅ Optimal for structure preservation |
| sentence-transformers | >=2.2.0 | Local embeddings | ✅ No API costs, good quality |
| chromadb | >=0.4.0 | Vector store | ✅ Persistent, fast, local |
| litellm | >=1.0.0 | LLM interface | ✅ Unified API for generation |
| rank-bm25 | >=0.2.2 | Sparse retrieval | ✅ Standard BM25 implementation |
| pytest | >=7.0.0 | Testing | ✅ Standard Python testing |

### Performance Benchmarking Approach

**Target**: <500ms for 1000 documents

**Measurement Points**:
1. Query embedding time: ~5-10ms (sentence-transformers on CPU)
2. Vector search time: ~20-50ms (ChromaDB HNSW with 1000 docs)
3. BM25 search time: ~10-20ms (rank-bm25 on 1000 chunks)
4. Result merging/filtering: ~1-5ms
5. **Total estimated**: ~40-85ms well under 500ms target

**Validation Strategy**:
- Create test dataset of 1000 markdown files
- Run query performance tests in test_ducklake_retrieval.py
- Monitor with time.perf_counter() at each stage
- Log P50, P95, P99 latencies

## Best Practices

### ChromaDB Optimization
- Use cosine similarity (default) for normalized embeddings
- Enable HNSW indexing for >100 documents
- Persist directory on local SSD for performance
- Single collection per engine instance for simplicity

### Sentence-Transformers Best Practices
- Use all-MiniLM-L6-v2 (default) for speed/quality balance
- Enable batch encoding with batch_size=32
- Keep model loaded in memory during batch operations
- Use convert_to_tensor=False to avoid GPU dependency

### Markdown Chunking Best Practices
- Target 200-500 tokens per chunk (configurable)
- Overlap of 50 tokens between chunks for context
- Preserve code fences (```) as atomic units
- Include parent headers in chunk metadata

### Testing Strategy
- Unit tests: Each component in isolation with mocks
- Integration tests: Full ingest→query→retrieve flow
- Quality tests: Manual review of chunking on sample docs
- Performance tests: Benchmark against 1000-doc collection

## Open Questions (None)

All technical unknowns resolved through clarification session and existing codebase analysis.

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Mistune Markdown Parser](https://mistune.lepture.com/)

---

**Status**: ✅ Research Complete
**Next Phase**: Phase 1 - Design & Contracts
