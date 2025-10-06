"""Tests for the RAG engine."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.engine import RAGEngine, create_rag_from_yaml, create_rag_from_config, load_config


@pytest.fixture
def temp_config():
    """Create a temporary config file."""
    config_content = """
chunking:
  strategy: "markdown_headers"
  max_chunk_size: 512
  overlap: 50

embedding:
  provider: "sentence_transformers"
  model: "all-MiniLM-L6-v2"

vector_store:
  type: "chromadb"
  persist_directory: "./data/chroma_db"
  collection_name: "test_documents"
  distance_metric: "cosine"

generation:
  provider: "openai"
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 512
  top_k: 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_components():
    """Mock all RAG engine components."""
    with patch('src.engine.MarkdownChunker') as mock_chunker, \
         patch('src.engine.EmbedderFactory') as mock_embedder_factory, \
         patch('src.engine.ChromaDBStore') as mock_store, \
         patch('src.engine.Retriever') as mock_retriever, \
         patch('src.engine.Generator') as mock_generator:

        # Setup mocks
        mock_chunker_instance = Mock()
        mock_chunker.return_value = mock_chunker_instance

        mock_embedder = Mock()
        mock_embedder.get_dimension.return_value = 384
        mock_embedder_factory.create_embedder.return_value = mock_embedder

        mock_store_instance = Mock()
        mock_store_instance.count.return_value = 10
        mock_store.return_value = mock_store_instance

        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance

        mock_generator_instance = Mock()
        mock_generator.return_value = mock_generator_instance

        yield {
            'chunker': mock_chunker_instance,
            'embedder': mock_embedder,
            'store': mock_store_instance,
            'retriever': mock_retriever_instance,
            'generator': mock_generator_instance
        }


def test_engine_initialization(temp_config, mock_components):
    """Test RAG engine initialization."""
    engine = create_rag_from_yaml(config_path=temp_config)

    assert engine.config is not None
    assert engine.chunker is not None
    assert engine.embedder is not None
    assert engine.vector_store is not None
    assert engine.retriever is not None
    assert engine.generator is not None


def test_ingest_document(temp_config, mock_components):
    """Test document ingestion."""
    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Test\n\nContent here.")
        temp_doc = f.name

    try:
        # Setup mocks
        from src.chunker import Chunk
        mock_chunk = Chunk(
            text="# Test\n\nContent here.",
            metadata={'source': 'test.md', 'position': 0}
        )
        mock_components['chunker'].chunk_document.return_value = [mock_chunk]
        mock_components['embedder'].embed_batch.return_value = [[0.1, 0.2, 0.3]]

        engine = create_rag_from_yaml(config_path=temp_config)
        num_chunks = engine.ingest_document(temp_doc)

        # Verify chunking was called
        mock_components['chunker'].chunk_document.assert_called_once()

        # Verify embedding was called
        mock_components['embedder'].embed_batch.assert_called_once()

        # Verify storage was called
        mock_components['store'].add.assert_called_once()

        assert num_chunks == 1

    finally:
        os.unlink(temp_doc)


def test_ingest_text(temp_config, mock_components):
    """Test text ingestion."""
    from src.chunker import Chunk

    mock_chunk = Chunk(
        text="Test content",
        metadata={'source': 'text_input', 'position': 0}
    )
    mock_components['chunker'].chunk_document.return_value = [mock_chunk]
    mock_components['embedder'].embed_batch.return_value = [[0.1, 0.2, 0.3]]

    engine = create_rag_from_yaml(config_path=temp_config)
    num_chunks = engine.ingest_text("Test content", source_name="test")

    assert num_chunks == 1
    mock_components['store'].add.assert_called_once()


def test_query(temp_config, mock_components):
    """Test querying without generation."""
    mock_results = [
        {'document': 'Result 1', 'metadata': {}, 'distance': 0.1},
        {'document': 'Result 2', 'metadata': {}, 'distance': 0.2}
    ]
    mock_components['retriever'].retrieve.return_value = mock_results

    engine = create_rag_from_yaml(config_path=temp_config)
    results = engine.query("test query", top_k=2)

    mock_components['retriever'].retrieve.assert_called_once_with("test query", top_k=2)
    assert results == mock_results


def test_generate_answer(temp_config, mock_components):
    """Test answer generation."""
    mock_context = [
        {'document': 'Context 1', 'metadata': {}, 'distance': 0.1}
    ]
    mock_components['retriever'].retrieve.return_value = mock_context
    mock_components['generator'].generate.return_value = "Generated answer"

    engine = create_rag_from_yaml(config_path=temp_config)
    answer = engine.generate_answer("test query")

    assert answer == "Generated answer"
    mock_components['retriever'].retrieve.assert_called_once()
    mock_components['generator'].generate.assert_called_once()


def test_get_stats(temp_config, mock_components):
    """Test getting engine statistics."""
    engine = create_rag_from_yaml(config_path=temp_config)
    stats = engine.get_stats()

    assert 'total_chunks' in stats
    assert 'embedding_dimension' in stats
    assert 'config' in stats
    assert stats['total_chunks'] == 10
    assert stats['embedding_dimension'] == 384


def test_clear(temp_config, mock_components):
    """Test clearing the vector store."""
    engine = create_rag_from_yaml(config_path=temp_config)
    engine.clear()

    mock_components['store'].clear.assert_called_once()


def test_config_env_substitution(mock_components):
    """Test environment variable substitution in config."""
    config_content = """
embedding:
  provider: "openai"
  api_key: "${TEST_API_KEY}"

generation:
  provider: "openai"
  model: "gpt-3.5-turbo"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        # Set environment variable
        os.environ['TEST_API_KEY'] = 'test-key-123'

        engine = create_rag_from_yaml(config_path=temp_path)

        # Check that env var was substituted
        assert engine.config['embedding']['api_key'] == 'test-key-123'

    finally:
        os.unlink(temp_path)
        if 'TEST_API_KEY' in os.environ:
            del os.environ['TEST_API_KEY']


def test_dependency_injection():
    """Test that RAG engine accepts injected dependencies."""
    from src.chunker import MarkdownChunker
    from src.generator import Generator

    # Create mock dependencies
    mock_chunker = Mock(spec=MarkdownChunker)
    mock_embedder = Mock()
    mock_embedder.get_dimension.return_value = 384
    mock_store = Mock()
    mock_store.count.return_value = 5
    mock_generator = Mock(spec=Generator)

    # Create engine with injected dependencies
    config = {'test': 'config'}
    engine = RAGEngine(
        chunker=mock_chunker,
        embedder=mock_embedder,
        vector_store=mock_store,
        generator=mock_generator,
        config=config
    )

    # Verify dependencies were injected correctly
    assert engine.chunker is mock_chunker
    assert engine.embedder is mock_embedder
    assert engine.vector_store is mock_store
    assert engine.generator is mock_generator
    assert engine.config == config


def test_create_rag_from_config(mock_components):
    """Test creating RAG engine from config dictionary."""
    config = {
        'chunking': {
            'max_chunk_size': 256,
            'overlap': 25
        },
        'embedding': {
            'provider': 'sentence_transformers',
            'model': 'all-MiniLM-L6-v2'
        },
        'vector_store': {
            'persist_directory': './test_db',
            'collection_name': 'test',
            'distance_metric': 'cosine'
        },
        'generation': {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.5,
            'max_tokens': 256
        }
    }

    engine = create_rag_from_config(config)

    assert engine is not None
    assert engine.config == config
    assert engine.chunker is not None
    assert engine.embedder is not None
    assert engine.vector_store is not None
    assert engine.generator is not None
