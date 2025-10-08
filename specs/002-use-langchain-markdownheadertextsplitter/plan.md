
# Implementation Plan: LangChain MarkdownHeaderTextSplitter Integration

**Branch**: `002-use-langchain-markdownheadertextsplitter` | **Date**: 2025-10-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-use-langchain-markdownheadertextsplitter/spec.md`

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
Replace the current custom mistune-based markdown chunker with LangChain's MarkdownHeaderTextSplitter to better preserve document hierarchical context. This will improve query result accuracy by ensuring chunks retain clear header context (e.g., "Configuration → Database → Connection Pooling"). The migration requires manual re-ingestion of existing documents with updated chunk size (1024 chars, 100 char overlap) and maintains <500ms query performance.

## Technical Context
**Language/Version**: Python 3.13
**Primary Dependencies**: langchain-text-splitters, mistune (removal planned), ChromaDB, sentence-transformers, LiteLLM
**Storage**: ChromaDB (persistent vector store), JSON metadata serialization
**Testing**: pytest with >80% coverage target
**Target Platform**: Cross-platform (macOS, Linux, Windows) via Python
**Project Type**: single (Python library + CLI)
**Performance Goals**: Maintain <500ms query latency for collections up to 1000 documents
**Constraints**: Chunks max 1024 chars with 100 char overlap; no automatic migration (manual re-ingestion required)
**Scale/Scope**: Local RAG system for tech documentation, designed for individual developer use

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**TDD Requirements**:
- ✅ All tests must be written first and reviewed before implementation
- ✅ RED-GREEN-REFACTOR cycle mandatory
- ✅ Use real implementations in tests (no mocks unless blocking)
- ✅ Tests must be behavior-focused, not implementation-focused

**Simplicity & YAGNI**:
- ✅ Replace existing chunker entirely (no dual-chunker complexity)
- ✅ Use LangChain's proven implementation (don't reinvent)
- ✅ Minimal configuration changes (leverage existing config structure)
- ✅ No speculative features beyond spec requirements

**Coverage & Quality**:
- ✅ Maintain >80% test coverage requirement
- ✅ Contract tests for chunker interface changes
- ✅ Integration tests for end-to-end chunking flow

**Status**: PASS - Approach follows TDD, YAGNI, and existing architectural patterns

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
├── chunker.py              # MODIFIED: Replace mistune logic with LangChain
├── embedder.py             # No changes
├── vector_store.py         # No changes (already supports JSON metadata)
├── retriever.py            # No changes
├── generator.py            # No changes
└── engine.py               # No changes

tests/
├── test_chunker.py         # MODIFIED: Update tests for new chunker behavior
├── test_embedder.py        # No changes
├── test_retriever.py       # No changes
└── test_engine.py          # MODIFIED: Integration tests for new chunking

config/
└── config.yaml             # MODIFIED: Update chunk_size: 1024, overlap: 100

pyproject.toml              # MODIFIED: Add langchain-text-splitters dependency
main.py                     # No changes
```

**Structure Decision**: Single project structure. This is a focused refactor of the chunking layer only. All changes isolated to `src/chunker.py` and related tests, minimizing blast radius. The existing architecture (embedder, vector store, retriever, generator, engine) remains unchanged.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
3. Apply TDD ordering: Tests → Implementation → Validation

**Task Categories**:

**Setup & Preparation** (Tasks 1-3):
- T001: Update pyproject.toml with langchain-text-splitters dependency
- T002: Update config.yaml with new chunk size (1024) and overlap (100)
- T003: Update .python-version if needed

**Contract Tests - RED Phase** (Tasks 4-10) [P]:
- T004: Write chunker constructor default tests
- T005: Write chunk dataclass interface tests
- T006: Write metadata structure tests
- T007: Write header hierarchy structure tests
- T008: Write chunk size constraint tests
- T009: Write headerless document handling tests
- T010: Write empty input handling tests

**Implementation - GREEN Phase** (Tasks 11-13):
- T011: Refactor src/chunker.py to use LangChain MarkdownHeaderTextSplitter
- T012: Remove old mistune-based chunking logic
- T013: Verify all contract tests pass

**Integration Tests** (Tasks 14-16):
- T014: Write end-to-end ingestion test with header preservation
- T015: Write query result header display test
- T016: Write headerless document integration test

**Validation & Documentation** (Tasks 17-20):
- T017: Execute quickstart.md validation
- T018: Run performance benchmark (verify <500ms)
- T019: Run full test suite (verify >80% coverage)
- T020: Update CLAUDE.md with LangChain integration notes

**Ordering Strategy**:
- **TDD Strict**: Contract tests (T004-T010) before implementation (T011-T013)
- **Dependency Order**: Setup → Tests → Implementation → Integration → Validation
- **Parallel Execution**: Mark [P] for independent test files (T004-T010 can run in parallel)

**Estimated Output**: ~20 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: No violations. Approach follows TDD, YAGNI, and simplicity principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |


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
- [x] Complexity deviations documented (none)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
