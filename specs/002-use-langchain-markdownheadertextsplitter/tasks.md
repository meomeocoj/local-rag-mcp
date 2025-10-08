# Tasks: LangChain MarkdownHeaderTextSplitter Integration

**Feature**: 002-use-langchain-markdownheadertextsplitter
**Input**: Design documents from `/specs/002-use-langchain-markdownheadertextsplitter/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.13, langchain-text-splitters, pytest, TDD approach
2. Load design documents:
   → data-model.md: Chunk entity with enhanced metadata
   → contracts/chunker_interface.md: 8 contract tests specified
   → research.md: LangChain integration decisions
   → quickstart.md: 10-step validation scenario
3. Generate tasks by category:
   → Setup: dependencies, config updates
   → Tests (RED): contract tests, integration tests
   → Core (GREEN): chunker refactor, cleanup
   → Validation: quickstart execution, benchmarks
4. Apply TDD ordering:
   → All tests written first (MUST FAIL)
   → Implementation makes tests pass (GREEN)
   → Refactor while keeping tests green
5. Number tasks sequentially (T001-T020)
6. Mark [P] for parallel execution (different test files)
7. SUCCESS: 20 dependency-ordered tasks ready
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions
- TDD strictly enforced: Tests before implementation

---

## Phase 3.1: Setup & Configuration

- [x] **T001** Add `langchain-text-splitters>=0.3.0` to dependencies in `pyproject.toml`
  - **File**: `pyproject.toml`
  - **Action**: Add to `[project.dependencies]` section
  - **Validation**: Run `uv sync --all-extras` successfully

- [x] **T002** Update chunk size and overlap in `config/config.yaml`
  - **File**: `config/config.yaml`
  - **Changes**:
    - `chunking.max_chunk_size: 512` → `1024`
    - `chunking.overlap: 50` → `100`
  - **Validation**: Config loads without errors

- [x] **T003** Verify Python 3.13 in `.python-version`
  - **File**: `.python-version`
  - **Action**: Ensure contains `3.13` or `3.13.0`
  - **Validation**: `python --version` shows 3.13.x

---

## Phase 3.2: Tests First (TDD RED Phase) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation in Phase 3.3**

### Contract Tests (from contracts/chunker_interface.md)

- [x] **T004** [P] Write contract test: chunker constructor defaults in `tests/test_chunker.py`
  - **Test**: `test_chunker_constructor_defaults()`
  - **Validates**: `max_chunk_size=1024`, `overlap=100`, `strategy="headers"`
  - **Expected**: FAIL (current defaults are 512, 50)

- [x] **T005** [P] Write contract test: Chunk dataclass structure in `tests/test_chunker.py`
  - **Test**: `test_chunk_dataclass_structure()`
  - **Validates**: Chunk has `text` and `metadata` fields
  - **Expected**: PASS (interface unchanged)

- [x] **T006** [P] Write contract test: metadata required fields in `tests/test_chunker.py`
  - **Test**: `test_chunk_metadata_required_fields()`
  - **Validates**: All chunks have `headers`, `position`, `source` in metadata
  - **Expected**: PASS (structure compatible)

- [x] **T007** [P] Write contract test: header metadata structure in `tests/test_chunker.py`
  - **Test**: `test_header_metadata_structure()`
  - **Validates**: Headers are list of dicts with `level` (int) and `text` (str)
  - **Expected**: FAIL (current structure different)

- [x] **T008** [P] Write contract test: chunk size constraint in `tests/test_chunker.py`
  - **Test**: `test_chunk_size_constraint()`
  - **Validates**: No chunk exceeds `max_chunk_size` (1024 chars)
  - **Expected**: FAIL (need to test with LangChain)

- [x] **T009** [P] Write contract test: position ordering in `tests/test_chunker.py`
  - **Test**: `test_chunk_position_ordering()`
  - **Validates**: Chunks ordered by position, starting at 0
  - **Expected**: PASS (existing behavior)

- [x] **T010** [P] Write contract test: source metadata propagation in `tests/test_chunker.py`
  - **Test**: `test_source_metadata_propagation()`
  - **Validates**: Source parameter flows to all chunk metadata
  - **Expected**: PASS (existing behavior)

- [x] **T011** [P] Write contract test: headerless document handling in `tests/test_chunker.py`
  - **Test**: `test_headerless_document_handling()`
  - **Validates**: Small headerless doc returns single chunk with empty headers list
  - **Expected**: FAIL (need LangChain fallback logic)

- [x] **T012** [P] Write contract test: empty input handling in `tests/test_chunker.py`
  - **Test**: `test_empty_input_returns_empty_list()`
  - **Validates**: Empty text returns `[]`
  - **Expected**: PASS (existing behavior)

### Integration Tests

- [x] **T013** [P] Write integration test: header hierarchy preservation in `tests/test_engine.py`
  - **Test**: `test_langchain_header_hierarchy_end_to_end()`
  - **Scenario**: Ingest markdown with H1→H2→H3, verify metadata structure in retrieved chunks
  - **Expected**: FAIL (requires LangChain implementation)

- [x] **T014** [P] Write integration test: query result header display in `tests/test_engine.py`
  - **Test**: `test_query_results_display_header_context()`
  - **Scenario**: Query ingested doc, verify header hierarchy formatted as "H1 → H2 → H3"
  - **Expected**: FAIL (requires metadata deserialization)

- [x] **T015** [P] Write integration test: large section chunking in `tests/test_engine.py`
  - **Test**: `test_large_section_chunks_with_overlap()`
  - **Scenario**: Section >1024 chars splits correctly with 100 char overlap
  - **Expected**: FAIL (requires LangChain recursive splitting)

---

## Phase 3.3: Core Implementation (GREEN Phase - ONLY after tests are failing)

**GATE: Verify T004-T015 are RED (failing) before proceeding**

- [x] **T016** Refactor `src/chunker.py` to use LangChain MarkdownHeaderTextSplitter
  - **File**: `src/chunker.py`
  - **Actions**:
    1. Import `from langchain_text_splitters import MarkdownHeaderTextSplitter`
    2. Replace `_chunk_by_headers()` implementation with LangChain splitter
    3. Update constructor defaults: `max_chunk_size=1024`, `overlap=100`
    4. Convert LangChain Document objects to internal Chunk format
    5. Preserve metadata structure: `headers`, `position`, `source`
  - **Validation**: T004, T007, T008, T011, T013, T015 turn GREEN

- [x] **T017** Remove deprecated chunking strategies from `src/chunker.py`
  - **File**: `src/chunker.py`
  - **Actions**:
    1. Remove `_chunk_by_paragraphs()` method
    2. Remove `_chunk_semantic()` method
    3. Remove `_chunk_recursive()` method
    4. Keep only `_chunk_by_headers()` (now using LangChain)
  - **Validation**: No broken imports, tests still GREEN

- [x] **T018** Verify all contract tests pass (GREEN state confirmation)
  - **Command**: `uv run pytest tests/test_chunker.py -v`
  - **Expected**: All 9 contract tests (T004-T012) PASS
  - **If FAIL**: Debug and fix `src/chunker.py` until GREEN

---

## Phase 3.4: Validation & Polish

- [ ] **T019** Execute quickstart.md validation (Steps 1-10)
  - **File**: `specs/002-use-langchain-markdownheadertextsplitter/quickstart.md`
  - **Actions**: Follow all 10 steps
  - **Validation**: All success criteria met (header display, performance <500ms)

- [ ] **T020** Run performance benchmark script
  - **Command**: `uv run python benchmark.py`
  - **Validation**: P95 latency <500ms (FR-011), no regression

- [x] **T021** Run full test suite and verify coverage >80%
  - **Command**: `uv run pytest tests/ --cov=src --cov-report=term-missing`
  - **Validation**: Coverage ≥80%, all tests PASS

- [x] **T022** Update CLAUDE.md with migration notes
  - **File**: `CLAUDE.md`
  - **Actions**: Add section on LangChain chunker, manual re-ingestion requirement
  - **Validation**: Document is clear and accurate

---

## Dependencies

### Critical Path (Sequential)
```
T001, T002, T003 (Setup)
    ↓
T004-T015 (Tests - RED Phase) [All must be written and FAILING]
    ↓
T016 (Implementation - GREEN Phase)
    ↓
T017 (Cleanup)
    ↓
T018 (Verify GREEN)
    ↓
T019, T020, T021, T022 (Validation)
```

### Detailed Dependencies
- **T001-T003**: No dependencies (can run in parallel)
- **T004-T015**: Depend on T001-T003 (need dependencies installed)
- **T016**: BLOCKS on T004-T015 (TDD: tests first)
- **T017**: BLOCKS on T016 (refactor after implementation works)
- **T018**: BLOCKS on T017 (verify no regressions)
- **T019-T022**: BLOCK on T018 (validation after all tests GREEN)

### Parallel Execution Opportunities
- **T001-T003**: Can run in parallel (different files)
- **T004-T015**: Can run in parallel (different test methods, independent)
- **T019-T022**: Can run in parallel (different validation activities)

---

## Parallel Execution Examples

### Phase 3.1 (Setup) - All Parallel
```bash
# Run T001, T002, T003 together
Task: "Add langchain-text-splitters>=0.3.0 to pyproject.toml"
Task: "Update chunk_size=1024, overlap=100 in config/config.yaml"
Task: "Verify Python 3.13 in .python-version"
```

### Phase 3.2 (Contract Tests) - All Parallel
```bash
# Run T004-T012 together (9 contract tests)
Task: "Write contract test: chunker constructor defaults in tests/test_chunker.py"
Task: "Write contract test: Chunk dataclass structure in tests/test_chunker.py"
Task: "Write contract test: metadata required fields in tests/test_chunker.py"
Task: "Write contract test: header metadata structure in tests/test_chunker.py"
Task: "Write contract test: chunk size constraint in tests/test_chunker.py"
Task: "Write contract test: position ordering in tests/test_chunker.py"
Task: "Write contract test: source metadata propagation in tests/test_chunker.py"
Task: "Write contract test: headerless document handling in tests/test_chunker.py"
Task: "Write contract test: empty input handling in tests/test_chunker.py"
```

### Phase 3.2 (Integration Tests) - All Parallel
```bash
# Run T013-T015 together (3 integration tests)
Task: "Write integration test: header hierarchy preservation in tests/test_engine.py"
Task: "Write integration test: query result header display in tests/test_engine.py"
Task: "Write integration test: large section chunking in tests/test_engine.py"
```

### Phase 3.4 (Validation) - All Parallel
```bash
# Run T019-T022 together (validation activities)
Task: "Execute quickstart.md validation (Steps 1-10)"
Task: "Run performance benchmark script"
Task: "Run full test suite and verify coverage >80%"
Task: "Update CLAUDE.md with migration notes"
```

---

## Task Checklist Summary

### Setup (3 tasks)
- [x] Dependencies
- [x] Configuration
- [x] Environment

### Tests - RED Phase (12 tasks)
- [x] 9 Contract Tests (T004-T012)
- [x] 3 Integration Tests (T013-T015)

### Implementation - GREEN Phase (3 tasks)
- [x] LangChain Refactor (T016)
- [x] Cleanup (T017)
- [x] Verification (T018)

### Validation (4 tasks)
- [x] Quickstart (T019)
- [x] Benchmark (T020)
- [x] Coverage (T021)
- [x] Documentation (T022)

**Total**: 22 tasks

---

## Notes

### TDD Enforcement
- **RED**: T004-T015 must be written and FAIL before T016
- **GREEN**: T016 makes failing tests pass
- **REFACTOR**: T017 cleans up while keeping tests GREEN

### Parallel Execution
- Tasks marked [P] can run simultaneously
- Same file tasks (e.g., multiple tests in `test_chunker.py`) can still run in parallel if test methods are independent
- Different files always safe to parallel

### Verification Gates
- After T003: Verify environment ready
- After T015: Verify all tests RED (failing)
- After T018: Verify all tests GREEN (passing)
- After T022: Verify feature complete

### Commit Strategy
- Commit after each phase completion:
  - After T003: "chore: setup dependencies and config"
  - After T015: "test: add contract and integration tests (RED)"
  - After T018: "feat: integrate LangChain MarkdownHeaderTextSplitter (GREEN)"
  - After T022: "docs: update documentation for LangChain migration"

---

## Troubleshooting

### If Tests Don't Turn GREEN
1. Check LangChain installation: `uv run python -c "import langchain_text_splitters; print('OK')"`
2. Verify config updated: `cat config/config.yaml | grep -A 3 chunking`
3. Debug specific test: `uv run pytest tests/test_chunker.py::test_name -v -s`
4. Review research.md for implementation guidance

### If Performance Regresses
1. Run benchmark: `uv run python benchmark.py`
2. Profile chunking: Add timing logs to `src/chunker.py`
3. Check chunk count: May have changed with new splitter
4. Review chunk size distribution: Ensure not exceeding 1024 chars

### If Coverage Drops
1. Run coverage: `uv run pytest --cov=src --cov-report=html`
2. Open `htmlcov/index.html` to see uncovered lines
3. Add unit tests for uncovered code paths
4. Focus on error handling and edge cases

---

**Status**: ✅ Tasks ready for execution. Start with T001.
