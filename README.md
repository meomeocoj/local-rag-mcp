# Local RAG MCP

A minimal Retrieval-Augmented Generation (RAG) engine with persistent storage for tech & project documentation, designed for AI Agent coding tools.

## Features

- 📝 **Markdown Chunking**: Intelligent chunking based on document structure (headers, code blocks)
- 🔢 **Dual Embedding Support**: Local embeddings (sentence-transformers) or API-based (OpenAI)
- 💾 **Persistent Vector Storage**: ChromaDB with automatic persistence
- 🔍 **Semantic Search**: Fast retrieval of relevant document chunks
- 🤖 **LLM Integration**: Unified LLM interface via LiteLLM (OpenAI, Anthropic, Cohere, etc.)
- 🧪 **Comprehensive Tests**: >80% test coverage
- 🖥️ **CLI Interface**: Easy-to-use command-line tools

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| Chunking | mistune |
| Embedding | sentence-transformers (local) + openai (API fallback) |
| Vector Store | ChromaDB |
| Generation | LiteLLM |
| Testing | pytest |

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd local-rag-mcp

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Configuration

Edit `config/config.yaml` to configure the RAG engine:

```yaml
chunking:
  strategy: "markdown_headers"
  max_chunk_size: 512
  overlap: 50

embedding:
  provider: "sentence_transformers"  # or "openai"
  model: "all-MiniLM-L6-v2"
  # For OpenAI:
  # endpoint: "https://api.openai.com/v1/embeddings"
  # api_key: "${OPENAI_API_KEY}"

vector_store:
  type: "chromadb"
  persist_directory: "./data/chroma_db"
  collection_name: "documents"
  distance_metric: "cosine"

generation:
  provider: "openai"  # LiteLLM supports: openai, anthropic, cohere, etc.
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 512
  top_k: 3  # Number of chunks to retrieve
```

### Environment Variables

Set API keys via environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or use a `.env` file with python-dotenv.

## Usage

### CLI Commands

#### Ingest Documents

```bash
# Ingest a markdown file
python main.py ingest path/to/document.md

# Ingest with custom source name
python main.py ingest path/to/document.md --source-name "My Project Docs"
```

#### Query (Retrieval Only)

```bash
# Search for relevant chunks
python main.py query "What is RAG?"

# Specify number of results
python main.py query "What is RAG?" --top-k 5
```

#### Generate Answers

```bash
# Generate an answer using RAG
python main.py generate "How do I implement RAG?"

# Stream the response
python main.py generate "How do I implement RAG?" --stream

# Use custom system prompt
python main.py generate "Explain RAG" --system-prompt "You are a technical expert."
```

#### Statistics

```bash
# Get engine statistics
python main.py stats
```

#### Clear Data

```bash
# Clear all stored data
python main.py clear

# Skip confirmation
python main.py clear --confirm
```

### Programmatic Usage

```python
from src.engine import RAGEngine

# Initialize the engine
engine = RAGEngine(config_path="config/config.yaml")

# Ingest documents
num_chunks = engine.ingest_document("path/to/document.md")
print(f"Ingested {num_chunks} chunks")

# Query without generation
results = engine.query("What is RAG?", top_k=3)
for result in results:
    print(result['document'])

# Generate answers
answer = engine.generate_answer("What is RAG?")
print(answer)

# Stream answers
for chunk in engine.generate_answer_stream("What is RAG?"):
    print(chunk, end='', flush=True)

# Get statistics
stats = engine.get_stats()
print(f"Total chunks: {stats['total_chunks']}")
```

## Project Structure

```
local-rag-mcp/
├── src/
│   ├── __init__.py
│   ├── chunker.py          # Markdown chunking
│   ├── embedder.py         # Embedding interface + implementations
│   ├── vector_store.py     # Vector store interface + ChromaDB
│   ├── retriever.py        # Search & retrieval logic
│   ├── generator.py        # LLM generation via LiteLLM
│   └── engine.py           # Main RAG engine orchestrator
├── tests/
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   └── test_engine.py
├── config/
│   └── config.yaml         # Configuration file
├── data/
│   ├── documents/          # Input markdown files
│   └── chroma_db/          # Persistent vector store
├── pyproject.toml
└── main.py                 # CLI/API entry point
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_engine.py
```

## Architecture

### Core Components

1. **Chunker (`src/chunker.py`)**
   - Parses markdown with mistune
   - Splits by headers (H1, H2, H3)
   - Preserves code blocks
   - Returns chunks with metadata (header hierarchy, position)

2. **Embedder (`src/embedder.py`)**
   - Abstract interface for embeddings
   - Implementations: SentenceTransformer, OpenAI
   - Factory pattern for easy switching

3. **Vector Store (`src/vector_store.py`)**
   - Abstract interface for vector storage
   - ChromaDB implementation with persistence
   - Methods: add, search, delete, persist, load

4. **Retriever (`src/retriever.py`)**
   - Encodes queries using embedder
   - Searches vector store
   - Returns top-k results with scores

5. **Generator (`src/generator.py`)**
   - Uses LiteLLM for unified LLM interface
   - Formats prompts with context + query
   - Supports streaming and batch responses

6. **Engine (`src/engine.py`)**
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

## Development

### Adding a New Embedder

1. Implement `EmbedderInterface` in `src/embedder.py`
2. Add factory method in `EmbedderFactory`
3. Update configuration schema

### Adding a New Vector Store

1. Implement `VectorStoreInterface` in `src/vector_store.py`
2. Update engine initialization in `src/engine.py`

## Limitations & Future Work

- Currently supports only markdown documents
- No re-ranking of retrieval results
- Single collection per engine instance
- Limited metadata filtering

### Potential Enhancements

- [ ] Support for PDF, HTML, and other formats
- [ ] Advanced chunking strategies (semantic, recursive)
- [ ] Re-ranking with cross-encoders
- [ ] Multi-query retrieval
- [ ] Metadata filtering in queries
- [ ] Web UI/API server
- [ ] Docker support

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Acknowledgments

Built with:
- [mistune](https://github.com/lepture/mistune) - Markdown parser
- [sentence-transformers](https://www.sbert.net/) - Local embeddings
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [LiteLLM](https://litellm.ai/) - Unified LLM interface
