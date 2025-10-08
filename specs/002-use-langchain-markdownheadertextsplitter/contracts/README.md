# Contracts: LangChain MarkdownHeaderTextSplitter Integration

**Feature**: 002-use-langchain-markdownheadertextsplitter
**Date**: 2025-10-07

## Overview

This directory contains API contracts for the LangChain MarkdownHeaderTextSplitter integration feature. Contracts define the stable interfaces that components must adhere to.

---

## Contract Files

### 1. [chunker_interface.md](chunker_interface.md)

**Purpose**: Defines the public API contract for the `MarkdownChunker` class.

**Scope**:
- Constructor signature and parameters
- `chunk_document()` method interface
- `Chunk` dataclass structure
- Metadata format and validation rules
- Contract tests (TDD RED phase)

**Consumers**:
- `src/engine.py` (primary consumer)
- `tests/test_chunker.py` (contract tests)
- `tests/test_engine.py` (integration tests)

---

## Contract Principles

### 1. Interface Stability

**Goal**: Minimize breaking changes to preserve compatibility with existing code.

**Applied**:
- `chunk_document()` signature unchanged
- `Chunk` dataclass interface unchanged
- `engine.py` requires no modifications to chunker calls

### 2. Test-Driven Development

**Goal**: Contracts include comprehensive test specifications.

**Applied**:
- All contract tests defined before implementation
- Tests must fail initially (RED state)
- Implementation makes tests pass (GREEN state)

### 3. Clear Validation Rules

**Goal**: Explicit constraints on data structures.

**Applied**:
- Chunk size limits documented (≤1024 chars)
- Metadata required fields specified
- Header structure validation rules defined

---

## Using These Contracts

### For Implementation

1. **Read Contract**: Understand interface requirements from contract docs
2. **Write Tests**: Implement contract tests (make them fail)
3. **Implement**: Write code to satisfy contract (make tests pass)
4. **Verify**: Run all contract tests to confirm compliance

### For Integration

1. **Review Contract**: Check if consuming code matches contract expectations
2. **Update Consumers**: Modify calls if contract changed (noted as "MODIFIED")
3. **Test Integration**: Verify end-to-end flow with new implementation

---

## Change Management

### Tracking Changes

Each contract document includes a **Changes from Current** section listing:
- **UNCHANGED**: No modifications required
- **MODIFIED**: Interface or behavior changed
- **NEW**: New field/parameter added

### Breaking vs Non-Breaking

**Breaking Changes** (require consumer updates):
- Signature changes (parameter types, return types)
- Removed fields or methods
- Modified validation rules that reject previously valid data

**Non-Breaking Changes** (safe to deploy):
- New optional parameters with defaults
- Additional metadata fields (backward compatible)
- Performance improvements
- Internal implementation swaps

---

## Contract Test Execution

### Location

All contract tests are implemented in:
- `tests/test_chunker.py` (chunker contract tests)
- `tests/test_engine.py` (integration contract tests)

### Running Tests

```bash
# Run all contract tests
uv run pytest tests/test_chunker.py -v

# Run specific contract test
uv run pytest tests/test_chunker.py::test_chunk_dataclass_structure -v

# Run with coverage
uv run pytest tests/test_chunker.py --cov=src.chunker --cov-report=term-missing
```

### Expected TDD Flow

1. **RED**: All contract tests fail (chunker not yet refactored)
2. **GREEN**: Implement LangChain integration to make tests pass
3. **REFACTOR**: Clean up code while keeping tests green

---

## Contract Versioning

**Current Version**: 1.0 (Initial LangChain integration)

**Version History**:
- 1.0 (2025-10-07): Initial contract for LangChain MarkdownHeaderTextSplitter

**Future Versions**:
- 1.1: Potential additions (e.g., custom header parsing rules)
- 2.0: Breaking changes (e.g., new chunking strategies)

---

## Related Documents

- [Data Model](../data-model.md): Entity definitions and relationships
- [Research](../research.md): Technical decisions and rationale
- [Quickstart](../quickstart.md): User-facing validation scenarios

---

**Status**: ✅ Contracts defined. Ready for TDD implementation.
