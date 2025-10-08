# Data Model: RAG Engine for Local Markdown Documents

**Date**: 2025-10-06
**Feature**: 001-the-rag-engine

## Core Entities

### 1. MarkdownDocument

**Purpose**: Represents a single markdown file from local storage

**Attributes**:
- `file_path`: str - Absolute path to the source .md file
- `content`: str - Raw markdown content
- `file_size`: int - Size in bytes
- `last_modified`: float - Unix timestamp of file modification
- `ingestion_timestamp`: float - Unix timestamp when ingested

**Validation Rules**:
- `file_path` must exist and be readable
- `file_path` must have `.md` extension
- `content` must not be empty
- `file_size` must be > 0

**State Transitions**:
```
[File on disk] → [Ingested] → [Chunked] → [Embedded] → [Indexed]
                      ↓
                [Can be deleted from index]
```

**Relationships**:
- Has many `DocumentChunk` (1:N relationship)

---

### 2. DocumentChunk

**Purpose**: Logically segmented portion of a markdown document, atomic unit for retrieval

**Attributes**:
- `chunk_id`: str - Unique identifier (UUID)
- `document_id`: str - Reference to source document (file_path hash)
- `content`: str - The chunk text content
- `start_pos`: int - Character position in original document
- `end_pos`: int - Character position in original document
- `header_hierarchy`: List[str] - Parent headers [H1, H2, H3, ...]
- `chunk_index`: int - Sequential position within document (0-based)
- `token_count`: int - Approximate number of tokens

**Metadata** (stored with chunk):
- `source_file`: str - Original file path
- `header_path`: str - Concatenated headers (e.g., "# Overview → ## Installation")
- `contains_code`: bool - Whether chunk contains code blocks
- `code_language`: Optional[str] - Language if single code block dominant

**Validation Rules**:
- `content` must not be empty
- `start_pos` < `end_pos`
- `chunk_index` >= 0
- `header_hierarchy` can be empty list (for pre-header content)
- `token_count` should be 50-1000 (configurable, soft limit)

**Relationships**:
- Belongs to one `MarkdownDocument` (N:1 relationship)
- Has one `Embedding` (1:1 relationship)

---

### 3. Query

**Purpose**: Natural language question or search phrase from user

**Attributes**:
- `query_text`: str - The user's query
- `timestamp`: float - Unix timestamp of query
- `embedding`: List[float] - Vector representation of query

**Validation Rules**:
- `query_text` must not be empty
- `query_text` length should be 3-500 characters (reasonable bounds)

**Lifecycle**:
```
[User input] → [Validated] → [Embedded] → [Used for search] → [Discarded]
```

**Relationships**:
- Produces many `RetrievalResult` (1:N relationship)

---

### 4. RetrievalResult

**Purpose**: Ranked chunk returned in response to a query

**Attributes**:
- `chunk`: DocumentChunk - The retrieved chunk object
- `similarity_score`: float - Cosine similarity score (0.0-1.0)
- `rank`: int - Position in results (1-5)
- `score_breakdown`: Dict[str, float] - Dense and sparse scores
  - `dense_score`: float - Semantic similarity score
  - `sparse_score`: float - BM25 score (if hybrid retrieval used)
  - `combined_score`: float - Final weighted score

**Validation Rules**:
- `similarity_score` must be >= 0.5 (threshold requirement)
- `similarity_score` must be <= 1.0
- `rank` must be 1-5
- `chunk` must not be None

**Lifecycle**:
```
[Query] → [Vector search] → [Score filtering] → [Ranking] → [RetrievalResult] → [Returned to user]
```

**Display Format** (for user):
```
Rank: {rank}
Score: {similarity_score:.2f}
Source: {chunk.metadata.source_file}
Section: {chunk.metadata.header_path}

{chunk.content}
---
```

---

## Supporting Entities

### 5. Embedding

**Purpose**: Vector representation of text for semantic search

**Attributes**:
- `vector`: List[float] - Dense embedding (dimension = model-specific, e.g., 384 for all-MiniLM-L6-v2)
- `model_name`: str - Embedding model used (e.g., "all-MiniLM-L6-v2")
- `created_at`: float - Unix timestamp

**Validation Rules**:
- `vector` dimension must match model output
- `vector` values are normalized (unit length for cosine similarity)

**Relationships**:
- Belongs to one `DocumentChunk` OR one `Query`

---

### 6. VectorIndex

**Purpose**: Persistent storage of embeddings with efficient search

**Attributes**:
- `collection_name`: str - ChromaDB collection identifier
- `persist_directory`: str - File system path for persistence
- `distance_metric`: str - Similarity metric (default: "cosine")
- `num_documents`: int - Count of indexed documents
- `num_chunks`: int - Count of indexed chunks

**Operations**:
- `add(chunks: List[DocumentChunk], embeddings: List[Embedding])` - Batch insert
- `search(query_embedding: Embedding, top_k: int = 5)` - Vector similarity search
- `delete(document_id: str)` - Remove all chunks from a document
- `persist()` - Save to disk
- `load()` - Load from disk

**Validation Rules**:
- `collection_name` must be valid identifier (alphanumeric + underscore)
- `persist_directory` must exist and be writable
- `num_chunks` must be >= 0

---

## Entity Relationships Diagram

```
MarkdownDocument (1) ────────┐
                             │
                             │ has many
                             ↓
                      DocumentChunk (N) ─────── has one ────→ Embedding (1)
                             │                                      │
                             │ indexed in                           │ stored in
                             ↓                                      ↓
                      VectorIndex ←──────────────────────────────┘


Query (1) ────── has one ────→ Embedding (1) ────── used for search ────→ VectorIndex
  │                                                                             │
  │ produces many                                                              │
  ↓                                                                             │
RetrievalResult (N) ←──────────── retrieves chunks from ──────────────────────┘
  │
  │ contains one
  ↓
DocumentChunk
```

---

## Data Flows

### Ingestion Flow

```
1. User provides file_path(s)
2. Create MarkdownDocument(file_path, content=read(file_path))
3. Validate MarkdownDocument
4. Chunker.chunk(document) → List[DocumentChunk]
5. For each chunk:
   a. Validate DocumentChunk
   b. Embedder.embed(chunk.content) → Embedding
   c. VectorIndex.add(chunk, embedding)
6. VectorIndex.persist()
```

### Query Flow

```
1. User provides query_text
2. Create Query(query_text)
3. Validate Query
4. Embedder.embed(query.query_text) → query_embedding
5. VectorIndex.search(query_embedding, top_k=5) → List[chunk_id, score]
6. Filter results where score >= 0.5
7. For each result:
   a. Fetch DocumentChunk by chunk_id
   b. Create RetrievalResult(chunk, score, rank)
8. Sort by score descending
9. Return List[RetrievalResult] (max 5)
```

### Deletion Flow

```
1. User provides document_id (or file_path)
2. VectorIndex.delete(document_id)
3. VectorIndex.persist()
4. Return confirmation
```

---

## Configuration Schema

**Config file**: `config/config.yaml`

```yaml
chunking:
  strategy: "header-based"  # Fixed for this feature
  max_chunk_size: 500       # tokens
  overlap: 50               # tokens

embedding:
  provider: "sentence_transformers"
  model: "all-MiniLM-L6-v2"
  batch_size: 32

vector_store:
  type: "chromadb"
  persist_directory: "data/chroma_db"
  collection_name: "markdown_docs"
  distance_metric: "cosine"

retrieval:
  top_k: 5                  # Fixed per requirements
  similarity_threshold: 0.5 # Fixed per requirements
  use_hybrid: true          # Dense + sparse retrieval
```

---

## Validation & Constraints Summary

| Entity | Key Constraints |
|--------|-----------------|
| MarkdownDocument | File exists, .md extension, content not empty |
| DocumentChunk | 50-1000 tokens, start_pos < end_pos, content not empty |
| Query | 3-500 characters, not empty |
| RetrievalResult | Score >= 0.5, rank 1-5, chunk not None |
| Embedding | Vector dimension matches model, normalized |
| VectorIndex | Collection name valid, directory writable |

---

**Status**: ✅ Data Model Complete
**Next**: Generate API contracts from functional requirements
