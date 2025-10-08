
# Implementation Plan: Optimized RAG Engine for Local Markdown Documents

**Branch**: `001-the-rag-engine` | **Date**: 2025-10-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-the-rag-engine/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Build an optimized RAG engine for local markdown documentation with <500ms query performance for up to 1000 documents. The system ingests markdown files while preserving structure (headers, code blocks, tables), chunks content intelligently at logical boundaries, and returns up to 5 semantically ranked results filtered by 0.5 similarity threshold. Features include batch ingestion, manual document deletion, and persistent storage across sessions.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: mistune (Markdown parsing), sentence-transformers (embeddings), ChromaDB (vector store), LiteLLM (LLM interface), rank-bm25 (sparse retrieval)
**Storage**: ChromaDB persistent vector store (local files in data/chroma_db/)
**Testing**: pytest with >80% coverage target
**Target Platform**: Local development environment (macOS/Linux/Windows)
**Project Type**: Single project (library + CLI)
**Performance Goals**: <500ms query response time for collections up to 1000 documents
**Constraints**: Local-only execution, no network dependencies for core functionality (except optional OpenAI embeddings)
**Scale/Scope**: Up to 1000 markdown documents, 5 results per query, 0.5 similarity threshold

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### TDD Compliance
- [ ] Tests written before implementation (RED phase)
- [ ] Tests fail initially (proving they test real behavior)
- [ ] Implementation only adds code to pass tests (GREEN phase)
- [ ] Refactoring preserves passing tests

### Library-First Architecture
- [x] Core functionality in src/ as standalone library
- [x] CLI in main.py wraps library
- [x] Components independently testable
- [x] Clear separation: chunker, embedder, retriever, generator, engine

### Simplicity (YAGNI & KISS)
- [x] No speculative features beyond requirements
- [x] Direct implementations (no premature abstractions)
- [x] Existing codebase already follows this principle

### Test Coverage
- [x] Target: >80% coverage (already established in pyproject.toml)
- [ ] Unit tests for each component
- [ ] Integration tests for full workflows
- [ ] Contract tests for interfaces

**Status**: ✅ PASS (existing architecture aligns with principles; TDD enforcement needed for new features)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
src/
├── __init__.py
├── chunker.py              # Markdown parsing & chunking logic
├── embedder.py             # Embedding interface + implementations
├── vector_store.py         # Vector store interface + ChromaDB impl
├── retriever.py            # Dense retrieval (semantic search)
├── sparse_retriever.py     # Sparse retrieval (BM25)
├── generator.py            # LLM generation via LiteLLM
└── engine.py               # Main RAG engine orchestrator

tests/
├── test_chunker.py         # Unit tests for chunking
├── test_embedder.py        # Unit tests for embeddings
├── test_retriever.py       # Unit tests for retrieval
├── test_engine.py          # Integration tests
├── test_chunking_quality.py # Quality tests for chunking
└── test_ducklake_retrieval.py # Retrieval quality tests

config/
└── config.yaml             # Configuration schema

data/
├── documents/              # Input markdown files
└── chroma_db/             # Persistent vector store

main.py                     # CLI entry point
```

**Structure Decision**: Single project structure with library-first architecture. All core logic in `src/` as independently testable modules. CLI in `main.py` provides thin wrapper around library API. Tests organized by component with dedicated quality/integration test files.

## Phase 0: Outline & Research

✅ **Completed**

**Research Areas Covered**:
1. Performance optimization for <500ms query response → Hybrid retrieval (dense + sparse)
2. Intelligent markdown chunking → Header-based hierarchical with context preservation
3. Similarity score filtering (0.5 threshold) → Post-retrieval filtering
4. Batch ingestion strategy → Multiple file paths with batch embedding
5. Manual document deletion → Explicit delete command, no auto-sync

**Key Decisions**:
- Use existing hybrid retrieval implementation (dense + sparse)
- Leverage mistune-based header-aware chunking (already implemented)
- ChromaDB with HNSW indexing for vector search
- sentence-transformers for local embeddings (no API costs)
- Batch embedding to amortize model load time

**Output**: [research.md](research.md) - All technical unknowns resolved

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

✅ **Completed**

**Entities Defined** ([data-model.md](data-model.md)):

- MarkdownDocument - Source file representation
- DocumentChunk - Atomic retrieval unit with hierarchy metadata
- Query - User search input
- RetrievalResult - Ranked search result
- Embedding - Vector representation
- VectorIndex - Persistent storage abstraction

**Contracts Created** ([contracts/](contracts/)):

- `chunker_contract.md` - Document chunking interface with 7 contract tests
- `retriever_contract.md` - Search interface with 10 contract tests
- `engine_contract.md` - Main orchestrator interface with 10 contract tests

**Test Scenarios Extracted** ([quickstart.md](quickstart.md)):

- 5 acceptance scenarios from feature spec
- End-to-end integration test script
- Performance validation procedures
- All functional requirements (FR-001 to FR-015) mapped to tests

**Agent Context Updated**:

- Executed `.specify/scripts/bash/update-agent-context.sh claude`
- Updated CLAUDE.md with Python 3.13, dependencies, and project type
- Preserved existing manual content

**Output**: data-model.md, contracts/, quickstart.md, CLAUDE.md updated

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

The `/tasks` command will:

1. Load `.specify/templates/tasks-template.md` as the base structure
2. Generate tasks from Phase 1 artifacts:
   - From `contracts/chunker_contract.md` → 7 test tasks + 1 implementation task
   - From `contracts/retriever_contract.md` → 10 test tasks + 1 implementation task
   - From `contracts/engine_contract.md` → 10 test tasks + 1 implementation task
   - From `data-model.md` → Validation tasks for entity constraints
   - From `quickstart.md` → 5 integration test tasks (acceptance scenarios)

3. Apply TDD ordering:
   - Phase A: Write all contract tests (must fail initially)
   - Phase B: Implement to make tests pass
   - Phase C: Integration tests for end-to-end scenarios
   - Phase D: Performance validation and optimization

**Ordering Strategy**:

```text
TDD Phase A: Contract Tests (All must fail before implementation)
├── [P] Task 001: Write chunker contract tests (7 tests)
├── [P] Task 002: Write retriever contract tests (10 tests)
├── [P] Task 003: Write engine contract tests (10 tests)
└── [P] Task 004: Run all tests → verify RED state

TDD Phase B: Implementation (Make tests pass)
├── Task 005: Implement chunker enhancements for FR-002, FR-003
├── Task 006: Implement retriever filtering for FR-012, FR-013
├── Task 007: Implement engine batch ingestion for FR-014
├── Task 008: Implement engine deletion for FR-015
├── Task 009: Add performance monitoring for FR-011
└── Task 010: Run all tests → verify GREEN state

TDD Phase C: Integration Tests
├── [P] Task 011: Acceptance test - Basic query workflow
├── [P] Task 012: Acceptance test - Multi-file aggregation
├── [P] Task 013: Acceptance test - Code block preservation
├── [P] Task 014: Acceptance test - Structure preservation
├── [P] Task 015: Acceptance test - Re-ingestion updates
└── Task 016: Run integration tests → all scenarios pass

TDD Phase D: Performance & Quality
├── Task 017: Benchmark query performance (1000 docs)
├── Task 018: Verify <500ms response time (FR-011)
├── Task 019: Test threshold filtering edge cases
└── Task 020: Final validation against quickstart.md

[P] = Can be executed in parallel (independent tasks)
```

**Dependency Rules**:

- Tasks 001-004 must complete before Task 005
- Tasks 005-010 must be sequential (each builds on previous)
- Tasks 011-015 can run in parallel after Task 010
- Tasks 017-020 run after all functional tests pass

**Estimated Output**: ~20 numbered, ordered tasks in tasks.md

**Key Principles**:

- **RED first**: All contract tests written and failing before any implementation
- **GREEN next**: Minimal implementation to pass each test
- **REFACTOR**: Clean up only after tests green
- **No new features**: Only implement what tests demand (YAGNI)

**IMPORTANT**: This phase is executed by the `/tasks` command, NOT by `/plan`

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

**Artifacts Generated**:

- [x] research.md - Technology decisions and best practices
- [x] data-model.md - Entity definitions and relationships
- [x] contracts/chunker_contract.md - Chunking interface with tests
- [x] contracts/retriever_contract.md - Retrieval interface with tests
- [x] contracts/engine_contract.md - Engine interface with tests
- [x] quickstart.md - Acceptance scenarios and validation
- [x] CLAUDE.md - Updated agent context
- [x] tasks.md - 22 TDD-ordered implementation tasks

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
