# Tasks: Optimized RAG Engine for Local Markdown Documents

**Input**: Design documents from `/specs/001-the-rag-engine/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)

```text
1. Load plan.md from feature directory
   → Extract: Python 3.13, pytest, mistune, sentence-transformers, ChromaDB, LiteLLM
2. Load design documents:
   → data-model.md: 6 entities (MarkdownDocument, DocumentChunk, Query, RetrievalResult, Embedding, VectorIndex)
   → contracts/: 3 contracts (chunker, retriever, engine) with 27 total tests
   → quickstart.md: 5 acceptance scenarios
3. Generate tasks by category:
   → Setup: dependencies, linting
   → Tests: 27 contract tests + 5 integration tests = 32 tests
   → Core: chunker enhancements, retriever filtering, engine batch/delete
   → Integration: performance monitoring
   → Polish: benchmarking, validation
4. Apply TDD ordering: Tests → Implementation → Integration → Polish
5. Mark [P] for parallel: Different files, no dependencies
6. SUCCESS: 22 tasks ready for execution
```

---

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Setup

- [x] **T001** Verify Python 3.13 and uv package manager installed
- [x] **T002** Run `uv sync --all-extras` to install all dependencies
- [x] **T003** [P] Configure pytest with coverage settings in pyproject.toml (already exists, verify >80% target)

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (from contracts/)

- [ ] **T004** [P] Write chunker contract tests in `tests/test_chunker.py`:
  - Test 1: Basic chunking (file with headers → chunks with metadata)
  - Test 2: Code block preservation (code fences balanced)
  - Test 3: Header hierarchy tracking (nested headers captured)
  - Test 4: Chunk size limits (respects max_chunk_size)
  - Test 5: Overlap between chunks (adjacent chunks share content)
  - Test 6: Error - missing file (raises FileNotFoundError)
  - Test 7: Error - invalid extension (raises ValueError)

- [ ] **T005** [P] Write retriever contract tests in `tests/test_retriever.py`:
  - Test 1: Basic query returns results (RetrievalResult objects)
  - Test 2: Results sorted by score (descending order)
  - Test 3: Similarity threshold filtering (score >= 0.5)
  - Test 4: Top-K limit respected (max 5 results)
  - Test 5: Empty results when no matches (threshold not met)
  - Test 6: Result includes metadata (source_file, header_path, rank)
  - Test 7: Error on empty query (raises ValueError)
  - Test 8: Error when not initialized (raises RuntimeError)
  - Test 9: Hybrid retrieval score breakdown (dense + sparse scores)
  - Test 10: Query response time <500ms for 1000 docs

- [ ] **T006** [P] Write engine contract tests in `tests/test_engine.py`:
  - Test 1: Ingest single file (returns ingested_count=1)
  - Test 2: Batch ingest multiple files (handles list of paths)
  - Test 3: Ingest handles partial failure (valid files succeed, errors logged)
  - Test 4: Query returns results (up to 5, score >= 0.5)
  - Test 5: Query respects constraints (FR-012, FR-013)
  - Test 6: Query performance <500ms for 1000 docs (FR-011)
  - Test 7: Delete document (removes from index)
  - Test 8: Delete handles not found (graceful, returns not_found_ids)
  - Test 9: Persistence across sessions (reload engine finds data)
  - Test 10: Re-ingestion updates index (no duplicates)

- [ ] **T007** Run all contract tests with `uv run pytest tests/test_chunker.py tests/test_retriever.py tests/test_engine.py` → **VERIFY ALL FAIL (RED state)**

### Integration Tests (from quickstart.md)

- [ ] **T008** [P] Write integration test for Scenario 1: Basic query workflow in `tests/test_integration_basic_query.py`
  - Ingest 100 test markdown files
  - Query "how to configure authentication"
  - Assert: Returns up to 5 results, all score >= 0.5, includes source paths

- [ ] **T009** [P] Write integration test for Scenario 2: Multi-file aggregation in `tests/test_integration_multifile.py`
  - Ingest 3 Python-related files
  - Query "Python"
  - Assert: Results span multiple files, ranked together, no duplicates

- [ ] **T010** [P] Write integration test for Scenario 3: Code block preservation in `tests/test_integration_code_blocks.py`
  - Ingest file with code blocks
  - Query for code example
  - Assert: Code formatting preserved, fences balanced

- [ ] **T011** [P] Write integration test for Scenario 4: Structure preservation in `tests/test_integration_structure.py`
  - Ingest structured doc with headers, lists, tables
  - Query for specific section
  - Assert: Header hierarchy displayed, structure maintained

- [ ] **T012** [P] Write integration test for Scenario 5: Re-ingestion in `tests/test_integration_reingest.py`
  - Ingest file, query to verify
  - Update file, re-ingest
  - Assert: Updated content searchable, old content removed

- [ ] **T013** Run all integration tests with `uv run pytest tests/test_integration_*.py` → **VERIFY ALL FAIL (RED state)**

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Chunker Enhancements (FR-002, FR-003)

- [ ] **T014** Enhance chunker in `src/chunker.py` to pass contract tests:
  - Ensure header-based chunking preserves structure
  - Keep code blocks atomic (no mid-function splits)
  - Track header hierarchy in chunk metadata
  - Implement chunk size limit with overlap
  - Validate file extension and existence
  - Run `uv run pytest tests/test_chunker.py` → **VERIFY ALL PASS (GREEN state)**

### Retriever Filtering (FR-011, FR-012, FR-013)

- [ ] **T015** Enhance retriever in `src/retriever.py` to pass contract tests:
  - Implement similarity threshold filtering (>= 0.5)
  - Enforce top-k limit (max 5 results)
  - Return results sorted by score descending
  - Add hybrid retrieval score breakdown (dense + sparse)
  - Validate query input (non-empty, >= 3 chars)
  - Run `uv run pytest tests/test_retriever.py` → **VERIFY ALL PASS (GREEN state)**

### Engine Batch & Delete (FR-014, FR-015)

- [ ] **T016** Enhance engine in `src/engine.py` to pass contract tests:
  - Implement batch ingestion (accept List[str] file paths)
  - Handle partial failures gracefully (log errors, continue)
  - Implement manual delete by document_id
  - Support re-ingestion without duplicates (update existing)
  - Ensure persistence across sessions (ChromaDB persist)
  - Run `uv run pytest tests/test_engine.py` → **VERIFY ALL PASS (GREEN state)**

### CLI Updates

- [ ] **T017** Update CLI in `main.py` to support new features:
  - Modify `ingest` command to accept multiple file paths: `main.py ingest file1.md file2.md ...`
  - Add `delete` command: `main.py delete <document_id_or_path>`
  - Ensure query output shows: Rank, Score, Source, Section hierarchy
  - Test manually: `uv run python main.py ingest data/documents/*.md`

---

## Phase 3.4: Integration & Performance

- [ ] **T018** Add performance monitoring in `src/retriever.py`:
  - Import `time.perf_counter()` for latency tracking
  - Log query execution time at DEBUG level
  - Add performance assertion in retriever tests (< 500ms for 1000 docs)
  - Run `uv run pytest tests/test_retriever.py::test_search_meets_performance_requirement`

- [ ] **T019** Run all integration tests → **VERIFY ALL PASS**:
  - `uv run pytest tests/test_integration_*.py -v`
  - Ensure all 5 acceptance scenarios validated

---

## Phase 3.5: Polish & Validation

- [ ] **T020** [P] Create performance benchmark script `tests/benchmark_1000_docs.py`:
  - Generate 1000 test markdown files
  - Ingest all files
  - Run 10 sample queries
  - Measure P50, P95, P99 latency
  - Assert: P95 < 500ms

- [ ] **T021** [P] Run coverage report and ensure >80% coverage:
  - `uv run pytest --cov=src --cov-report=term-missing`
  - Check coverage for: chunker.py, retriever.py, engine.py, embedder.py
  - Add unit tests for any uncovered edge cases

- [ ] **T022** Execute quickstart validation in `specs/001-the-rag-engine/quickstart.md`:
  - Follow each acceptance scenario manually
  - Verify: batch ingestion, manual deletion, threshold filtering
  - Confirm: <500ms query time, up to 5 results, score >= 0.5

---

## Dependencies

### Critical Path (Must be Sequential)

```text
T001-T003 (Setup)
    ↓
T004-T006 (Write contract tests) [can run in parallel]
    ↓
T007 (Verify RED state) ← GATE: Must fail before continuing
    ↓
T008-T012 (Write integration tests) [can run in parallel]
    ↓
T013 (Verify RED state) ← GATE: Must fail before continuing
    ↓
T014 (Implement chunker) → T015 (Implement retriever) → T016 (Implement engine)
    ↓
T017 (Update CLI)
    ↓
T018 (Performance monitoring)
    ↓
T019 (Integration tests pass) ← GATE: Must pass before polish
    ↓
T020-T022 (Polish & validation) [can run in parallel]
```

### Blocking Relationships

- **T007 blocks T008-T013**: Cannot write integration tests until contract tests exist and fail
- **T013 blocks T014-T016**: Cannot implement until all tests are failing (TDD RED state)
- **T014 blocks T015**: Retriever depends on chunker producing correct chunks
- **T015 blocks T016**: Engine depends on retriever for query functionality
- **T016 blocks T017**: CLI depends on engine implementation
- **T019 blocks T020-T022**: Polish only after integration validated

---

## Parallel Execution Examples

### Phase 1: Contract Tests (T004-T006)

```bash
# Launch all contract test tasks in parallel (different test files):
uv run pytest tests/test_chunker.py &
uv run pytest tests/test_retriever.py &
uv run pytest tests/test_engine.py &
wait
```

### Phase 2: Integration Tests (T008-T012)

```bash
# Launch all integration test tasks in parallel (different test files):
uv run pytest tests/test_integration_basic_query.py &
uv run pytest tests/test_integration_multifile.py &
uv run pytest tests/test_integration_code_blocks.py &
uv run pytest tests/test_integration_structure.py &
uv run pytest tests/test_integration_reingest.py &
wait
```

### Phase 3: Polish (T020-T021)

```bash
# Launch benchmark and coverage in parallel:
python tests/benchmark_1000_docs.py &
uv run pytest --cov=src --cov-report=term-missing &
wait
```

---

## Notes

- **[P] tasks** = Different files, no dependencies, can run in parallel
- **TDD enforcement**: T007 and T013 are gates - all tests MUST fail before implementation
- **Performance requirement**: <500ms query time for 1000 documents (FR-011)
- **Quality requirement**: >80% test coverage
- **Commit strategy**: Commit after each task (especially after T007, T013, T016, T019)

---

## Validation Checklist

*Verified during task generation*

- [x] All contracts have corresponding tests (T004-T006: 27 tests total)
- [x] All entities represented in tests (MarkdownDocument, DocumentChunk, Query, RetrievalResult)
- [x] All tests come before implementation (T004-T013 before T014-T017)
- [x] Parallel tasks truly independent (different files, no shared state)
- [x] Each task specifies exact file path (src/chunker.py, tests/test_*.py, etc.)
- [x] No [P] task modifies same file as another [P] task
- [x] All functional requirements covered (FR-001 to FR-015)
- [x] All acceptance scenarios have tests (5 scenarios → T008-T012)

---

## Summary

**Total Tasks**: 22
**Parallel Groups**: 3 (contract tests, integration tests, polish)
**Critical Gates**: 2 (T007: RED state verification, T013: RED state verification)
**Estimated Completion**: ~6-8 hours (depending on existing code quality)

**Key Milestones**:

1. ✅ T007: All contract tests failing (RED)
2. ✅ T013: All integration tests failing (RED)
3. ✅ T016: All contract tests passing (GREEN)
4. ✅ T019: All integration tests passing (GREEN)
5. ✅ T022: Quickstart validation complete

---

**Status**: ✅ Tasks ready for execution
**Next**: Execute tasks in order, respecting dependencies and TDD gates
