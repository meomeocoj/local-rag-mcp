# Quickstart: LangChain MarkdownHeaderTextSplitter Integration

**Feature**: 002-use-langchain-markdownheadertextsplitter
**Date**: 2025-10-07
**Expected Duration**: 10 minutes

## Purpose

Validate the LangChain MarkdownHeaderTextSplitter integration by:
1. Installing updated dependencies
2. Migrating existing documents to new chunking
3. Verifying header context preservation in query results
4. Confirming performance requirements met

---

## Prerequisites

- Python 3.13 installed
- uv package manager installed
- Existing RAG system with documents (or sample docs provided)
- Terminal access

---

## Step 1: Install Dependencies

**Duration**: 2 minutes

### Action

```bash
# Navigate to project root
cd /Users/meomeocoj/AI/local-rag-mcp

# Install updated dependencies (includes langchain-text-splitters)
uv sync --all-extras
```

### Expected Output

```
Resolved XX packages in XXXms
Installed XX packages in XXXms
 + langchain-text-splitters==0.3.0
 ... (other dependencies)
```

### Validation

```bash
# Verify langchain-text-splitters installed
uv run python -c "from langchain_text_splitters import MarkdownHeaderTextSplitter; print('✓ LangChain installed')"
```

**Expected**: `✓ LangChain installed`

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Import error | Run `uv sync --all-extras` again |
| Python version mismatch | Verify Python 3.13: `python --version` |

---

## Step 2: Backup Existing Data (Optional)

**Duration**: 1 minute

### Action

```bash
# Backup current vector store (optional but recommended)
cp -r data/chroma_db data/chroma_db.backup.$(date +%Y%m%d)
```

### Expected Output

```
# Directory copied
data/chroma_db.backup.20251007/
```

### Validation

```bash
ls -d data/chroma_db.backup.*
```

**Expected**: Backup directory listed

---

## Step 3: Clear Existing Chunks

**Duration**: 30 seconds

### Action

```bash
# Clear old chunks from vector store
uv run python main.py clear --confirm
```

### Expected Output

```
All data cleared successfully.
```

### Validation

```bash
# Verify empty vector store
uv run python main.py stats
```

**Expected**:
```
=== RAG Engine Statistics ===
Total chunks: 0
...
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Check file permissions on `data/chroma_db/` |
| Confirmation prompt | Use `--confirm` flag to skip prompt |

---

## Step 4: Create Test Document

**Duration**: 1 minute

### Action

```bash
# Create sample markdown with clear header hierarchy
cat > /tmp/test_langchain_chunking.md << 'EOF'
# API Documentation

Welcome to the API documentation.

## Authentication

All API requests require authentication.

### OAuth 2.0

Use OAuth 2.0 for secure authentication.

#### Setup

1. Register your application
2. Obtain client credentials
3. Request access token

### API Keys

Alternative authentication method using API keys.

## Rate Limiting

API requests are rate limited.

### Limits

- 100 requests per minute (free tier)
- 1000 requests per minute (pro tier)

### Handling Rate Limits

Implement exponential backoff when rate limited.
EOF
```

### Expected Output

```
# File created
/tmp/test_langchain_chunking.md
```

### Validation

```bash
cat /tmp/test_langchain_chunking.md | head -5
```

**Expected**: First 5 lines of document displayed

---

## Step 5: Ingest Test Document

**Duration**: 2 minutes

### Action

```bash
# Ingest document using new chunker
uv run python main.py ingest /tmp/test_langchain_chunking.md
```

### Expected Output

```
Successfully ingested 1 file(s), X chunks total
```

**Note**: Exact chunk count depends on chunker behavior

### Validation

```bash
# Check chunks were created
uv run python main.py stats
```

**Expected**:
```
=== RAG Engine Statistics ===
Total chunks: X  # Should be > 0
Embedding dimension: 1536
...
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No chunks created | Check file exists: `ls /tmp/test_langchain_chunking.md` |
| Import error | Verify dependencies: Step 1 |
| Embedding fails | Check config.yaml embedding settings |

---

## Step 6: Query with Header Context

**Duration**: 2 minutes

### Action

```bash
# Query for specific topic
uv run python main.py query "How do I use OAuth 2.0?"
```

### Expected Output

```
Query time: XX.XXms
Found X results (max 5, threshold >= 0.5):

Rank 1 | Score: 0.XX | Source: test_langchain_chunking.md
Section: API Documentation → Authentication → OAuth 2.0

### OAuth 2.0

Use OAuth 2.0 for secure authentication.

...
--------------------------------------------------------------------------------
```

### Validation Checklist

- [x] Query returns results (not "No results found")
- [x] **Section** field displays header hierarchy (e.g., "API Documentation → Authentication → OAuth 2.0")
- [x] Header hierarchy uses " → " separator (not garbled characters)
- [x] Query time <500ms (performance requirement)
- [x] Results sorted by score (Rank 1 has highest score)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "No results found" | Check embedding model is running; verify chunks ingested (Step 5) |
| Garbled header display | Verify metadata serialization fix in vector_store.py |
| Query time >500ms | Check collection size; run benchmark script |

---

## Step 7: Verify Header Hierarchy Preservation

**Duration**: 1 minute

### Action

```bash
# Query different header levels
uv run python main.py query "API rate limiting"
```

### Expected Output

```
Rank 1 | Score: 0.XX | Source: test_langchain_chunking.md
Section: API Documentation → Rate Limiting

## Rate Limiting

API requests are rate limited.
...
```

### Validation Checklist

- [x] Header context matches query topic
- [x] Hierarchy reflects document structure (H1 → H2 → H3)
- [x] Multiple header levels displayed correctly

---

## Step 8: Test Edge Case (Headerless Document)

**Duration**: 1 minute

### Action

```bash
# Create document without headers
cat > /tmp/test_no_headers.md << 'EOF'
This is a plain text document without any headers.
It should still be chunked correctly as a single chunk
since it's under 1024 characters.
EOF

# Ingest headerless document
uv run python main.py ingest /tmp/test_no_headers.md
```

### Expected Output

```
Successfully ingested 1 file(s), 1 chunks total
```

### Validation

```bash
# Query headerless document
uv run python main.py query "plain text document"
```

**Expected**:
```
Rank X | Score: 0.XX | Source: test_no_headers.md
Section: (empty or no section line)

This is a plain text document without any headers.
...
```

### Validation Checklist

- [x] Headerless document ingested without error
- [x] Single chunk created (document <1024 chars)
- [x] Query returns result
- [x] No crash or error when headers field is empty

---

## Step 9: Verify Performance

**Duration**: 1 minute (optional but recommended)

### Action

```bash
# Run performance benchmark (if available)
uv run python benchmark.py
```

### Expected Output

```
================================================================================
RAG Engine Performance Benchmark
================================================================================
...
================================================================================
FR-011 Compliance Check (<500ms requirement)
================================================================================
  P95 latency: XX.XXms
  Requirement: <500ms
  Status: ✓ PASS
...
```

### Validation Checklist

- [x] P95 latency <500ms
- [x] Query performance maintained
- [x] No regression from previous chunker

---

## Step 10: Clean Up

**Duration**: 30 seconds

### Action

```bash
# Remove test files
rm /tmp/test_langchain_chunking.md
rm /tmp/test_no_headers.md

# Optionally restore backup (if Step 2 was performed)
# rm -rf data/chroma_db
# mv data/chroma_db.backup.YYYYMMDD data/chroma_db
```

### Expected Output

```
# Files removed
```

---

## Success Criteria

### Must Pass (Critical)

- ✅ LangChain dependency installed successfully
- ✅ Documents ingest without errors
- ✅ Header hierarchy preserved in metadata
- ✅ Query results display "Section: H1 → H2 → H3" format
- ✅ Header text clean (not garbled characters)
- ✅ Query performance <500ms
- ✅ Headerless documents handled gracefully

### Should Pass (Important)

- ✅ Multiple header levels (H1-H6) supported
- ✅ Chunk size ≤1024 characters enforced
- ✅ Overlap between chunks (100 chars) functional
- ✅ All existing tests pass (run `uv run pytest tests/`)

### Nice to Have (Optional)

- ✅ Backup/restore process successful
- ✅ Benchmark script confirms performance
- ✅ Integration with existing documents seamless

---

## Rollback Procedure

If validation fails:

### 1. Restore Code

```bash
# Checkout previous version
git checkout main  # Or previous commit

# Reinstall dependencies
uv sync --all-extras
```

### 2. Restore Data

```bash
# Restore backup vector store
rm -rf data/chroma_db
mv data/chroma_db.backup.YYYYMMDD data/chroma_db
```

### 3. Verify Rollback

```bash
# Test original chunker
uv run python main.py query "test query"
```

---

## Troubleshooting

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Import error: `langchain_text_splitters` | Dependency not installed | Run `uv sync --all-extras` |
| Header display garbled | Metadata serialization issue | Check `vector_store.py` JSON deserialization |
| No results from query | Embedding mismatch | Clear and re-ingest documents |
| Query time >500ms | Large collection | Run benchmark; check hardware |
| Chunks exceed 1024 chars | Chunker config wrong | Verify `config.yaml` chunk_size: 1024 |

### Debug Commands

```bash
# Check dependency versions
uv run python -c "import langchain_text_splitters; print(langchain_text_splitters.__version__)"

# Inspect chunk metadata
uv run python -c "
from src.engine import create_rag_from_yaml
engine = create_rag_from_yaml()
results = engine.retriever.retrieve('test', top_k=1)
print(results[0] if results else 'No results')
"

# Verify config
cat config/config.yaml | grep -A 3 chunking
```

---

## Next Steps

After successful quickstart:

1. **Migrate Production Documents**:
   ```bash
   uv run python main.py clear --confirm
   uv run python main.py ingest data/documents/*.md
   ```

2. **Run Full Test Suite**:
   ```bash
   uv run pytest tests/ --cov=src --cov-report=term-missing
   ```

3. **Update Documentation**:
   - Update README.md with new chunking details
   - Document migration steps for users
   - Update CLAUDE.md with LangChain integration notes

4. **Monitor Performance**:
   - Run benchmark regularly
   - Track query latency metrics
   - Verify >80% test coverage maintained

---

## Acceptance

**Validated By**: _____________
**Date**: _____________
**Status**: [ ] Pass [ ] Fail
**Notes**:

---

**Status**: ✅ Quickstart ready for validation.
