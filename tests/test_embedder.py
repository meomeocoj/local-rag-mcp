"""Tests for the embedder module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.embedder import (
    EmbedderInterface,
    SentenceTransformerEmbedder,
    OpenAIEmbedder,
    EmbedderFactory
)


@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer model."""
    with patch('src.embedder.SentenceTransformer') as mock:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock.return_value = mock_model
        yield mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch('src.embedder.OpenAI') as mock:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


def test_sentence_transformer_embedder(mock_sentence_transformer):
    """Test SentenceTransformer embedder."""
    embedder = SentenceTransformerEmbedder(model_name="test-model")

    # Test single embedding
    embedding = embedder.embed_text("test text")
    assert isinstance(embedding, np.ndarray)

    # Test dimension
    dim = embedder.get_dimension()
    assert dim == 384


def test_sentence_transformer_batch(mock_sentence_transformer):
    """Test batch embedding with SentenceTransformer."""
    mock_sentence_transformer.return_value.encode.return_value = np.array([
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6]
    ])

    embedder = SentenceTransformerEmbedder()
    texts = ["text 1", "text 2"]

    embeddings = embedder.embed_batch(texts)

    assert isinstance(embeddings, list)
    assert len(embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in embeddings)


def test_openai_embedder(mock_openai_client):
    """Test OpenAI embedder."""
    embedder = OpenAIEmbedder(model_name="text-embedding-ada-002", api_key="test-key")

    # Test single embedding
    embedding = embedder.embed_text("test text")
    assert isinstance(embedding, np.ndarray)

    # Test dimension
    dim = embedder.get_dimension()
    assert dim == 1536  # Known dimension for ada-002


def test_openai_batch(mock_openai_client):
    """Test batch embedding with OpenAI."""
    mock_openai_client.return_value.embeddings.create.return_value.data = [
        Mock(embedding=[0.1, 0.2, 0.3]),
        Mock(embedding=[0.4, 0.5, 0.6])
    ]

    embedder = OpenAIEmbedder(api_key="test-key")
    texts = ["text 1", "text 2"]

    embeddings = embedder.embed_batch(texts)

    assert isinstance(embeddings, list)
    assert len(embeddings) == 2


def test_embedder_factory_sentence_transformers(mock_sentence_transformer):
    """Test factory creation of SentenceTransformer embedder."""
    embedder = EmbedderFactory.create_embedder(
        provider="sentence_transformers",
        model="test-model"
    )

    assert isinstance(embedder, SentenceTransformerEmbedder)


def test_embedder_factory_openai(mock_openai_client):
    """Test factory creation of OpenAI embedder."""
    embedder = EmbedderFactory.create_embedder(
        provider="openai",
        model="text-embedding-ada-002",
        api_key="test-key"
    )

    assert isinstance(embedder, OpenAIEmbedder)


def test_embedder_factory_invalid_provider():
    """Test factory with invalid provider."""
    with pytest.raises(ValueError, match="Unknown provider"):
        EmbedderFactory.create_embedder(provider="invalid")


def test_embedder_interface():
    """Test that embedders implement the interface."""
    # This is more of a structural test
    assert hasattr(EmbedderInterface, 'embed_text')
    assert hasattr(EmbedderInterface, 'embed_batch')
    assert hasattr(EmbedderInterface, 'get_dimension')
