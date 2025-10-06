# Local RAG MCP - Claude Development Guide

This document provides an overview of the project structure and development guidelines for AI assistants working on this codebase.

## Project Overview

Local RAG MCP is a minimal Retrieval-Augmented Generation (RAG) engine with persistent storage, designed for tech & project documentation in AI Agent coding tools. It combines intelligent document chunking, dual embedding support, and LLM integration to enable semantic search and answer generation.

## Technology Stack

- **Language**: Python 3.13
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (fast, reliable Python package management)
- **Chunking**: mistune (Markdown parsing)
- **Embedding**: sentence-transformers (local) + OpenAI (API fallback)
- **Vector Store**: ChromaDB (persistent vector storage)
- **Generation**: LiteLLM (unified LLM interface)
- **Testing**: pytest with >80% coverage

## Project Structure

```
local-rag-mcp/
├── src/                    # Core source code
│   ├── __init__.py
│   ├── chunker.py         # Markdown chunking logic
│   ├── embedder.py        # Embedding interface + implementations
│   ├── vector_store.py    # Vector store interface + ChromaDB impl
│   ├── retriever.py       # Search & retrieval logic
│   ├── generator.py       # LLM generation via LiteLLM
│   └── engine.py          # Main RAG engine orchestrator
├── tests/                  # Test suite
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   └── test_engine.py
├── config/                 # Configuration files
│   └── config.yaml        # Main configuration
├── data/                   # Data directory
│   ├── documents/         # Input markdown files
│   └── chroma_db/         # Persistent vector store
├── .python-version        # Python version (3.13)
├── pyproject.toml         # Project dependencies and metadata
├── main.py               # CLI/API entry point
└── README.md             # User documentation
```

## Development Setup

### Prerequisites
- Python 3.13
- uv package manager

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_engine.py
```

### Running the CLI

```bash
# Ingest documents
uv run python main.py ingest path/to/document.md

# Query
uv run python main.py query "What is RAG?"

# Generate answers
uv run python main.py generate "How do I implement RAG?"
```

## Architecture Overview

### Core Components

1. **Chunker** (`src/chunker.py`)
   - Parses markdown using mistune
   - Splits by headers (H1, H2, H3)
   - Preserves code blocks
   - Returns chunks with metadata (header hierarchy, position)

2. **Embedder** (`src/embedder.py`)
   - Abstract interface for embeddings
   - Implementations: SentenceTransformer (local), OpenAI (API)
   - Factory pattern for easy switching

3. **Vector Store** (`src/vector_store.py`)
   - Abstract interface for vector storage
   - ChromaDB implementation with persistence
   - Methods: add, search, delete, persist, load

4. **Retriever** (`src/retriever.py`)
   - Encodes queries using embedder
   - Searches vector store
   - Returns top-k results with scores

5. **Generator** (`src/generator.py`)
   - Uses LiteLLM for unified LLM interface
   - Formats prompts with context + query
   - Supports streaming and batch responses

6. **Engine** (`src/engine.py`)
   - Orchestrates all components
   - Handles configuration loading
   - Provides high-level API

### Data Flow

```
Document → Chunker → Embedder → Vector Store
                                      ↓
Query → Embedder → Retriever ← Vector Store
                      ↓
                  Generator → Answer
```

## Configuration

Configuration is managed via `config/config.yaml`:

- **Chunking**: Strategy, max chunk size, overlap
- **Embedding**: Provider (sentence_transformers/openai), model, API settings
- **Vector Store**: Type (chromadb), persist directory, collection name, distance metric
- **Generation**: Provider (openai/anthropic/cohere), model, temperature, max tokens, top_k

Environment variables (e.g., `OPENAI_API_KEY`) can be set via `.env` file.

## Development Guidelines

### Adding New Components

**New Embedder:**
1. Implement `EmbedderInterface` in `src/embedder.py`
2. Add factory method in `EmbedderFactory`
3. Update configuration schema
4. Add tests in `tests/test_embedder.py`

**New Vector Store:**
1. Implement `VectorStoreInterface` in `src/vector_store.py`
2. Update engine initialization in `src/engine.py`
3. Add tests

### Code Style
- Follow PEP 8 conventions
- Use type hints
- Write docstrings for public functions/classes
- Maintain test coverage >80%

### Testing
- Unit tests for each component
- Integration tests in `test_engine.py`
- Use pytest fixtures for setup/teardown
- Mock external dependencies (OpenAI API, etc.)

## Common Tasks

### Adding Support for New Document Formats
1. Create new chunker or extend existing one
2. Update `src/chunker.py`
3. Add tests
4. Update documentation

### Changing Embedding Model
1. Update `config/config.yaml`
2. Ensure embedder factory supports the model
3. Re-ingest documents if needed

### Debugging
- Check `config/config.yaml` for configuration issues
- Verify API keys in `.env` file
- Use `main.py stats` to check vector store state
- Enable debug logging in engine initialization

## Known Limitations

- Currently supports only markdown documents
- No re-ranking of retrieval results
- Single collection per engine instance
- Limited metadata filtering

## Future Enhancements

- Support for PDF, HTML, and other formats
- Advanced chunking strategies (semantic, recursive)
- Re-ranking with cross-encoders
- Multi-query retrieval
- Metadata filtering in queries
- Web UI/API server
- Docker support
