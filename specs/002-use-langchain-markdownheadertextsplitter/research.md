# Research: LangChain MarkdownHeaderTextSplitter Integration

**Feature**: 002-use-langchain-markdownheadertextsplitter
**Date**: 2025-10-07
**Status**: Complete

## Overview

Research findings for replacing the custom mistune-based markdown chunker with LangChain's MarkdownHeaderTextSplitter to preserve document hierarchical context.

---

## Decision 1: LangChain MarkdownHeaderTextSplitter vs Custom Implementation

**Decision**: Use LangChain's MarkdownHeaderTextSplitter

**Rationale**:
- **Battle-tested**: LangChain's splitter is widely used in production RAG systems
- **Maintained**: Active development and community support
- **Feature-rich**: Built-in support for header hierarchy preservation
- **Standards-compliant**: Handles CommonMark and GitHub Flavored Markdown
- **Simpler**: Eliminates need to maintain custom markdown parsing logic

**Alternatives Considered**:
1. **Keep custom mistune-based chunker**
   - Rejected: Current implementation doesn't preserve header context adequately
   - Rejected: Would require significant rework to match LangChain functionality

2. **Build custom header-aware splitter from scratch**
   - Rejected: Violates YAGNI principle
   - Rejected: Reinventing a solved problem
   - Rejected: Increases maintenance burden

**Implementation Details**:
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
    ("#####", "Header 5"),
    ("######", "Header 6"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False  # Keep headers in chunks for context
)
```

---

## Decision 2: Chunk Size Configuration

**Decision**: Increase chunk size to 1024 characters with 100 character overlap

**Rationale**:
- **Better Context**: Larger chunks capture more complete semantic units
- **Header Preservation**: Reduces likelihood of splitting mid-section
- **Embedding Models**: Most modern embedders (OpenAI, sentence-transformers) handle 512-1024 token chunks well
- **Performance**: Minimal impact on query latency (chunking happens at ingestion time)
- **Overlap Strategy**: 100 char overlap (~10%) provides good continuity without excessive duplication

**Alternatives Considered**:
1. **Keep 512 chars**
   - Rejected: Too small for preserving header context in technical docs
   - Rejected: Frequent mid-section splits reduce semantic coherence

2. **Use 2048+ chars**
   - Rejected: May exceed embedding model optimal range
   - Rejected: Reduces granularity of retrieval
   - Rejected: Not requested in requirements

**Current vs New**:
| Parameter | Current | New | Change |
|-----------|---------|-----|--------|
| Max Chunk Size | 512 | 1024 | +100% |
| Overlap | 50 | 100 | +100% |

---

## Decision 3: Header Metadata Structure

**Decision**: Store header hierarchy as JSON-serialized list of dicts

**Rationale**:
- **Consistency**: Matches existing vector store metadata serialization (already implemented)
- **Flexibility**: Preserves level information for future filtering/ranking
- **Display-Ready**: Easy to format for CLI output (e.g., "H1 → H2 → H3")
- **No Breaking Changes**: Existing JSON serialization in `vector_store.py` already supports this

**Structure**:
```python
{
    "headers": [
        {"level": 1, "text": "Configuration"},
        {"level": 2, "text": "Database"},
        {"level": 3, "text": "Connection Pooling"}
    ],
    "source": "config-guide.md",
    "position": 5
}
```

**Alternatives Considered**:
1. **Flat string representation**
   - Rejected: Loses level information
   - Rejected: Harder to query/filter by depth

2. **Custom binary format**
   - Rejected: Over-engineering
   - Rejected: Reduces debuggability

---

## Decision 4: Migration Strategy

**Decision**: Manual re-ingestion (no automatic migration)

**Rationale**:
- **Simplicity**: No migration tooling to build/maintain
- **Safety**: Users explicitly choose when to migrate
- **Clarity**: Clear separation between old and new chunked documents
- **Small Scale**: Target use case (individual developers) makes manual migration acceptable

**User Impact**:
- Users must run `main.py clear` then re-ingest documents
- Documented in quickstart and migration guide
- One-time operation per upgrade

**Alternatives Considered**:
1. **Automatic migration on startup**
   - Rejected: Spec explicitly requires manual re-ingestion (FR-005)
   - Rejected: Risk of data loss without user consent

2. **Side-by-side chunkers**
   - Rejected: Spec requires complete replacement (FR-007)
   - Rejected: Violates simplicity principle

---

## Decision 5: Handling Documents Without Headers

**Decision**: Treat headerless documents as single chunk (if ≤1024 chars) or split by character limit (if >1024 chars)

**Rationale**:
- **Graceful Degradation**: System doesn't reject valid markdown
- **Spec Compliance**: Matches FR-004 requirements
- **User Experience**: Predictable behavior for edge cases

**Implementation**:
```python
chunks = splitter.split_text(markdown_text)

if not chunks or (len(chunks) == 1 and len(chunks[0].page_content) > 1024):
    # Fallback: split by character limit
    return self._split_by_chars(markdown_text, chunk_size=1024, overlap=100)

return chunks  # Header-based chunks
```

**Alternatives Considered**:
1. **Reject headerless documents**
   - Rejected: Poor UX
   - Rejected: Valid markdown may lack headers

2. **Force paragraph-based splitting**
   - Rejected: Not specified in requirements
   - Rejected: Adds complexity

---

## Decision 6: Dependency Management

**Decision**: Add `langchain-text-splitters` as a direct dependency (not full `langchain`)

**Rationale**:
- **Minimal Footprint**: Only install the text splitter module
- **Faster Install**: `langchain-text-splitters` is ~5MB vs full `langchain` ~50MB
- **Clear Intent**: Explicit about what we're using
- **Version Pinning**: `langchain-text-splitters>=0.3.0`

**pyproject.toml Update**:
```toml
[project]
dependencies = [
    "langchain-text-splitters>=0.3.0",
    # ... existing deps
]
```

**Alternatives Considered**:
1. **Install full `langchain`**
   - Rejected: Unnecessary bloat
   - Rejected: Pulls in unused dependencies (LLM integrations, agents, etc.)

2. **Vendor the code**
   - Rejected: Loses upstream fixes/improvements
   - Rejected: Maintenance burden

---

## Decision 7: Testing Strategy

**Decision**: TDD with contract tests, unit tests, and integration tests

**Test Coverage**:
1. **Contract Tests** (`tests/test_chunker.py`):
   - Verify `Chunk` object structure unchanged
   - Assert header metadata format
   - Test chunk size constraints

2. **Unit Tests** (`tests/test_chunker.py`):
   - Header hierarchy preservation (H1 → H2 → H3)
   - Headerless document handling
   - Chunk size and overlap enforcement
   - Special element preservation (code blocks, tables, lists)

3. **Integration Tests** (`tests/test_engine.py`):
   - End-to-end ingestion with new chunker
   - Query results include correct header metadata
   - Display formatting in CLI output

**Rationale**:
- Follows TDD constitutional requirement
- Maintains >80% coverage target
- Tests behavior, not implementation details

---

## Decision 8: Backward Compatibility & Deprecation

**Decision**: Complete replacement (no backward compatibility)

**Rationale**:
- **Spec Requirement**: FR-007 mandates complete replacement
- **Simplicity**: No dual-chunker complexity
- **Clear Migration**: One-time cutover reduces confusion

**Removed Code**:
- Custom mistune AST parsing in `chunker.py`
- `_chunk_by_headers()` method (replaced by LangChain)
- `_join_tokens()` method (no longer needed)

**Preserved Code**:
- `Chunk` data class interface (keeps engine.py unchanged)
- Metadata structure (compatible with existing vector store)
- Configuration schema (extends existing `chunking` section)

---

## Technical Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| LangChain behavior differs from custom chunker | Medium | Medium | Comprehensive test suite covering edge cases |
| Performance regression | Low | Medium | Benchmark against existing <500ms requirement |
| Breaking change in LangChain API | Low | High | Pin to minor version; monitor releases |
| Header parsing edge cases | Medium | Low | Fallback to character-based splitting |

---

## Performance Benchmarks

**Expected Impact**:
- **Ingestion**: Minimal change (chunking is fast relative to embedding)
- **Query**: No change (chunking happens at ingestion time only)
- **Storage**: ~5-10% increase due to larger chunks and richer metadata
- **Memory**: Negligible (chunks processed in batches)

**Validation**:
- Run existing benchmark script (`benchmark.py`) post-implementation
- Verify <500ms query latency maintained (NFR-001)

---

## Open Questions

None - all clarifications resolved during spec phase.

---

## References

- [LangChain Text Splitters Docs](https://python.langchain.com/docs/modules/data_connection/document_transformers/markdown_header_metadata)
- [MarkdownHeaderTextSplitter API](https://api.python.langchain.com/en/latest/markdown/langchain_text_splitters.markdown.MarkdownHeaderTextSplitter.html)
- [RAG Chunking Best Practices](https://www.pinecone.io/learn/chunking-strategies/)

---

**Status**: ✅ All research complete. Ready for Phase 1 (Design & Contracts).
