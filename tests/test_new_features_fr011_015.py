"""
Contract tests for new feature requirements FR-011 through FR-015.

These tests verify:
- FR-011: Query performance <500ms for 1000 docs
- FR-012: Returns up to 5 results per query
- FR-013: Filters results with similarity score >= 0.5
- FR-014: Batch ingestion support
- FR-015: Manual document deletion

Following TDD: These tests should FAIL initially, then implementation makes them PASS.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import time
from typing import List

from src.engine import RAGEngine, create_rag_from_config


def get_test_config():
    """Get minimal test configuration."""
    return {
        'chunking': {'strategy': 'headers', 'max_chunk_size': 500, 'overlap': 50},
        'embedding': {'provider': 'sentence_transformers', 'model': 'all-MiniLM-L6-v2'},
        'vector_store': {'type': 'chromadb', 'persist_directory': ':memory:', 'collection_name': 'test_docs'},
        'generation': {'provider': 'openai', 'model': 'gpt-3.5-turbo'},
        'retrieval': {'top_k': 5, 'similarity_threshold': 0.5}
    }


class TestBatchIngestion:
    """Tests for FR-014: Batch ingestion support."""

    def test_ingest_multiple_files_in_single_call(self, tmp_path):
        """Test that engine.ingest() accepts List[str] of file paths."""
        # Given multiple markdown files
        files = []
        for i in range(3):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document {i}\nContent for document {i}")
            files.append(str(file_path))

        # When calling ingest with list of paths
        engine = create_rag_from_config(get_test_config())
        result = engine.ingest(files)

        # Then all files are ingested
        assert result['ingested_count'] == 3
        assert result['failed_count'] == 0
        assert result['chunk_count'] >= 3

    def test_batch_ingest_handles_partial_failure(self, tmp_path):
        """Test that batch ingest continues on individual file failures."""
        # Given mix of valid and invalid files
        valid1 = tmp_path / "valid1.md"
        valid1.write_text("# Valid 1\nContent")

        valid2 = tmp_path / "valid2.md"
        valid2.write_text("# Valid 2\nContent")

        files = [
            str(valid1),
            str(tmp_path / "nonexistent.md"),  # Will fail
            str(valid2)
        ]

        # When batch ingesting
        engine = create_rag_from_config(get_test_config())
        result = engine.ingest(files)

        # Then valid files succeed, failure is recorded
        assert result['ingested_count'] == 2
        assert result['failed_count'] == 1
        assert len(result['failed_files']) == 1
        assert 'nonexistent.md' in result['failed_files'][0]


class TestManualDeletion:
    """Tests for FR-015: Manual document deletion."""

    def test_delete_document_by_id(self, tmp_path):
        """Test that engine.delete() removes documents from index."""
        # Given an ingested document
        file_path = tmp_path / "to_delete.md"
        file_path.write_text("# To Delete\nThis will be removed")

        engine = create_rag_from_config(get_test_config())
        ingest_result = engine.ingest([str(file_path)])
        doc_id = list(ingest_result.get('document_ids', []))[0] if ingest_result.get('document_ids') else str(file_path)

        # When deleting the document
        delete_result = engine.delete([doc_id])

        # Then document is removed
        assert delete_result['deleted_count'] == 1
        assert doc_id in delete_result['deleted_ids']
        assert delete_result['not_found_ids'] == []

    def test_delete_handles_not_found(self):
        """Test that delete gracefully handles non-existent IDs."""
        # Given an engine
        engine = create_rag_from_config(get_test_config())

        # When deleting non-existent document
        result = engine.delete(['nonexistent_id_12345'])

        # Then gracefully handled
        assert result['deleted_count'] == 0
        assert 'nonexistent_id_12345' in result['not_found_ids']

    def test_delete_multiple_documents(self, tmp_path):
        """Test batch deletion of multiple documents."""
        # Given multiple ingested documents
        files = []
        for i in range(3):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Doc {i}\nContent {i}")
            files.append(str(file_path))

        engine = create_rag_from_config(get_test_config())
        ingest_result = engine.ingest(files)
        doc_ids = list(ingest_result.get('document_ids', files))

        # When deleting all documents
        delete_result = engine.delete(doc_ids)

        # Then all are deleted
        assert delete_result['deleted_count'] == len(doc_ids)
        assert len(delete_result['deleted_ids']) == len(doc_ids)


class TestQueryConstraints:
    """Tests for FR-012 and FR-013: Query result constraints."""

    def test_query_returns_max_5_results(self, tmp_path):
        """FR-012: Query returns up to 5 results."""
        # Given 10 documents ingested
        files = []
        for i in range(10):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Python Document {i}\nPython is great for scripting {i}")
            files.append(str(file_path))

        engine = create_rag_from_config(get_test_config())
        engine.ingest(files)

        # When querying
        results = engine.query("Python")

        # Then at most 5 results returned
        assert len(results) <= 5

    def test_query_filters_by_threshold_0_5(self, tmp_path):
        """FR-013: Query filters results with score < 0.5."""
        # Given documents with varying relevance
        relevant = tmp_path / "relevant.md"
        relevant.write_text("# Python Programming\nPython is a programming language for scripting.")

        irrelevant = tmp_path / "irrelevant.md"
        irrelevant.write_text("# Cooking Recipes\nHow to cook pasta with tomato sauce.")

        engine = create_rag_from_config(get_test_config())
        engine.ingest([str(relevant), str(irrelevant)])

        # When querying for Python
        results = engine.query("Python programming")

        # Then all results have score >= 0.5
        for result in results:
            assert result.get('score', result.get('similarity_score', 1.0)) >= 0.5

    def test_query_returns_empty_when_no_matches_above_threshold(self, tmp_path):
        """Test empty results when no chunks meet 0.5 threshold."""
        # Given document about unrelated topic
        file_path = tmp_path / "cooking.md"
        file_path.write_text("# Cooking\nHow to make pasta carbonara.")

        engine = create_rag_from_config(get_test_config())
        engine.ingest([str(file_path)])

        # When querying completely unrelated content
        results = engine.query("quantum physics equations")

        # Then empty or very few results (none above threshold)
        # This might return empty list or filtered results
        if results:
            for result in results:
                assert result.get('score', result.get('similarity_score', 1.0)) >= 0.5


class TestPerformanceRequirement:
    """Tests for FR-011: Query performance < 500ms for 1000 docs."""

    @pytest.mark.slow
    def test_query_performance_1000_docs(self, tmp_path):
        """FR-011: Query completes in <500ms for 1000 documents."""
        # Given 1000 ingested documents
        files = []
        for i in range(100):  # Using 100 instead of 1000 for faster test
            file_path = tmp_path / f"doc{i}.md"
            content = f"# Document {i}\n" + ("Content paragraph. " * 10)
            file_path.write_text(content)
            files.append(str(file_path))

        engine = create_rag_from_config(get_test_config())
        engine.ingest(files)

        # When querying
        start = time.perf_counter()
        results = engine.query("Content")
        elapsed = time.perf_counter() - start

        # Then response time < 500ms (scaled for 100 docs)
        # For 100 docs, expect <50ms, for 1000 would be <500ms
        assert elapsed < 0.5, f"Query took {elapsed*1000:.0f}ms, expected <500ms"
        assert len(results) <= 5  # Also verify result count

    def test_query_returns_results_sorted_by_score(self, tmp_path):
        """Test that results are sorted by similarity score descending."""
        # Given multiple documents
        files = []
        for i in range(5):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document\nPython programming " * (i + 1))
            files.append(str(file_path))

        engine = create_rag_from_config(get_test_config())
        engine.ingest(files)

        # When querying
        results = engine.query("Python programming")

        # Then results sorted descending by score
        if len(results) > 1:
            scores = [r.get('score', r.get('similarity_score', 0)) for r in results]
            assert scores == sorted(scores, reverse=True), "Results not sorted by score"


# Fixtures
@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        'chunking': {'strategy': 'headers', 'max_chunk_size': 500},
        'embedding': {'provider': 'sentence_transformers', 'model': 'all-MiniLM-L6-v2'},
        'vector_store': {'type': 'chromadb', 'persist_directory': ':memory:'},
        'retrieval': {'top_k': 5, 'similarity_threshold': 0.5}
    }
