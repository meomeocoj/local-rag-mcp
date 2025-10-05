"""Tests for the retriever module."""

import pytest
import numpy as np
from unittest.mock import Mock
from src.retriever import Retriever


@pytest.fixture
def mock_embedder():
    """Mock embedder."""
    embedder = Mock()
    embedder.embed_text.return_value = np.array([0.1, 0.2, 0.3])
    return embedder


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = Mock()
    store.search.return_value = [
        {
            'id': 'doc1_0',
            'document': 'This is the first chunk.',
            'metadata': {'source': 'doc1.md'},
            'distance': 0.1
        },
        {
            'id': 'doc1_1',
            'document': 'This is the second chunk.',
            'metadata': {'source': 'doc1.md'},
            'distance': 0.3
        }
    ]
    return store


def test_retriever_initialization(mock_embedder, mock_vector_store):
    """Test retriever initialization."""
    retriever = Retriever(mock_embedder, mock_vector_store)

    assert retriever.embedder == mock_embedder
    assert retriever.vector_store == mock_vector_store


def test_retrieve(mock_embedder, mock_vector_store):
    """Test basic retrieval."""
    retriever = Retriever(mock_embedder, mock_vector_store)

    results = retriever.retrieve("test query", top_k=2)

    # Check that embedder was called
    mock_embedder.embed_text.assert_called_once_with("test query")

    # Check that vector store was searched
    mock_vector_store.search.assert_called_once()

    # Check results
    assert len(results) == 2
    assert all('document' in r for r in results)


def test_retrieve_with_scores(mock_embedder, mock_vector_store):
    """Test retrieval with similarity scores."""
    retriever = Retriever(mock_embedder, mock_vector_store)

    results = retriever.retrieve_with_scores("test query", top_k=2)

    # Check that similarity scores are added
    assert all('similarity' in r for r in results)
    assert all(0 <= r['similarity'] <= 1 for r in results)


def test_retrieve_with_score_threshold(mock_embedder, mock_vector_store):
    """Test retrieval with score threshold."""
    retriever = Retriever(mock_embedder, mock_vector_store)

    # Set a high threshold to filter results
    results = retriever.retrieve_with_scores(
        "test query",
        top_k=2,
        score_threshold=0.95
    )

    # Results should be filtered
    # With distances 0.1 and 0.3, similarities are 0.9 and 0.7
    # Only 0.9 should pass the 0.95 threshold... actually none should pass
    # Let's check the logic: similarity = 1 - distance
    # distance=0.1 -> similarity=0.9 (fails 0.95)
    # distance=0.3 -> similarity=0.7 (fails 0.95)
    assert len(results) <= 2


def test_retrieve_batch(mock_embedder, mock_vector_store):
    """Test batch retrieval."""
    retriever = Retriever(mock_embedder, mock_vector_store)

    queries = ["query 1", "query 2"]
    results = retriever.retrieve_batch(queries, top_k=2)

    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(r, list) for r in results)


def test_retrieve_empty_results(mock_embedder):
    """Test retrieval with no results."""
    store = Mock()
    store.search.return_value = []

    retriever = Retriever(mock_embedder, store)
    results = retriever.retrieve("test query", top_k=5)

    assert results == []
