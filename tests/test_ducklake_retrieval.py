"""Test suite for evaluating DuckLake documentation retrieval quality."""

import pytest
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engine import create_rag_from_yaml, RAGEngine
from tests.ducklake_queries import DUCKLAKE_TEST_QUERIES, get_query_by_category


class RetrievalEvaluator:
    """Evaluates retrieval quality without LLM generation."""

    def __init__(self, engine: RAGEngine):
        self.engine = engine

    def evaluate_query(
        self,
        query: str,
        expected_keywords: List[str],
        expected_topics: List[str],
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval quality for a single query.

        Args:
            query: The search query
            expected_keywords: Keywords that should appear in relevant chunks
            expected_topics: Topics that should be covered
            top_k: Number of chunks to retrieve

        Returns:
            Dictionary with evaluation metrics
        """
        # Retrieve chunks
        results = self.engine.query(query, top_k=top_k)

        if not results:
            return {
                "query": query,
                "success": False,
                "error": "No results returned",
                "chunks_retrieved": 0
            }

        # Calculate metrics
        metrics = {
            "query": query,
            "chunks_retrieved": len(results),
            "avg_distance": sum(r["distance"] for r in results) / len(results),
            "min_distance": min(r["distance"] for r in results),
            "max_distance": max(r["distance"] for r in results),
            "keyword_matches": {},
            "chunks_with_keywords": 0,
            "keyword_coverage": 0.0,
            "results": []
        }

        # Check keyword presence in chunks
        keyword_found_in = {kw: [] for kw in expected_keywords}
        chunks_with_any_keyword = set()

        for i, result in enumerate(results):
            chunk_text = result["document"].lower()
            chunk_keywords_found = []

            for keyword in expected_keywords:
                if keyword.lower() in chunk_text:
                    keyword_found_in[keyword].append(i)
                    chunk_keywords_found.append(keyword)
                    chunks_with_any_keyword.add(i)

            # Store chunk info
            metrics["results"].append({
                "rank": i + 1,
                "distance": result["distance"],
                "source": result["metadata"].get("source", "unknown"),
                "keywords_found": chunk_keywords_found,
                "keyword_count": len(chunk_keywords_found),
                "preview": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
            })

        # Calculate keyword coverage
        metrics["keyword_matches"] = {
            kw: len(indices) for kw, indices in keyword_found_in.items()
        }
        keywords_found = sum(1 for kw, indices in keyword_found_in.items() if len(indices) > 0)
        metrics["keyword_coverage"] = keywords_found / len(expected_keywords) if expected_keywords else 0
        metrics["chunks_with_keywords"] = len(chunks_with_any_keyword)
        metrics["chunk_relevance_ratio"] = len(chunks_with_any_keyword) / len(results)

        # Overall assessment
        if metrics["chunk_relevance_ratio"] >= 0.6 and metrics["keyword_coverage"] >= 0.5:
            metrics["rating"] = "GOOD"
        elif metrics["chunk_relevance_ratio"] >= 0.4 and metrics["keyword_coverage"] >= 0.3:
            metrics["rating"] = "FAIR"
        else:
            metrics["rating"] = "POOR"

        metrics["success"] = True
        return metrics

    def print_evaluation(self, metrics: Dict[str, Any]) -> None:
        """Print evaluation results in a readable format."""
        print(f"\n{'='*80}")
        print(f"Query: {metrics['query']}")
        print(f"{'='*80}")

        if not metrics.get("success"):
            print(f"ERROR: {metrics.get('error')}")
            return

        print(f"\n📊 METRICS:")
        print(f"  Rating: {metrics['rating']}")
        print(f"  Chunks Retrieved: {metrics['chunks_retrieved']}")
        print(f"  Avg Distance: {metrics['avg_distance']:.3f}")
        print(f"  Keyword Coverage: {metrics['keyword_coverage']:.1%} ({sum(1 for v in metrics['keyword_matches'].values() if v > 0)}/{len(metrics['keyword_matches'])} keywords found)")
        print(f"  Relevant Chunks: {metrics['chunks_with_keywords']}/{metrics['chunks_retrieved']} ({metrics['chunk_relevance_ratio']:.1%})")

        print(f"\n🔑 KEYWORD MATCHES:")
        for keyword, count in metrics['keyword_matches'].items():
            status = "✓" if count > 0 else "✗"
            print(f"  {status} '{keyword}': {count} chunks")

        print(f"\n📄 TOP RESULTS:")
        for result in metrics['results'][:5]:  # Show top 5
            status = "✓" if result['keyword_count'] > 0 else "✗"
            print(f"\n  [{result['rank']}] {status} Distance: {result['distance']:.3f} | Keywords: {result['keyword_count']}")
            print(f"      Source: {result['source']}")
            if result['keywords_found']:
                print(f"      Found: {', '.join(result['keywords_found'][:5])}")
            print(f"      Preview: {result['preview'][:150]}...")


@pytest.fixture
def rag_engine():
    """Create RAG engine with test configuration."""
    config_path = "config/config.yaml"
    return create_rag_from_yaml(config_path=config_path)


@pytest.fixture
def evaluator(rag_engine):
    """Create retrieval evaluator."""
    return RetrievalEvaluator(rag_engine)


@pytest.mark.parametrize("test_query", DUCKLAKE_TEST_QUERIES, ids=[q["query"] for q in DUCKLAKE_TEST_QUERIES])
def test_ducklake_retrieval(evaluator, test_query, capsys):
    """Test retrieval quality for DuckLake queries."""
    metrics = evaluator.evaluate_query(
        query=test_query["query"],
        expected_keywords=test_query["expected_keywords"],
        expected_topics=test_query["expected_topics"],
        top_k=10
    )

    # Print detailed results
    evaluator.print_evaluation(metrics)

    # Assertions for test framework
    assert metrics["success"], f"Query failed: {metrics.get('error')}"
    assert metrics["chunks_retrieved"] > 0, "No chunks retrieved"

    # Quality thresholds
    if metrics["rating"] == "POOR":
        print(f"\n⚠️  WARNING: Query performance is POOR. Consider tuning configuration.")


def test_category_summary(evaluator):
    """Test and summarize results by category."""
    categories = ["factual", "conceptual", "procedural", "complex"]

    print(f"\n{'='*80}")
    print(f"CATEGORY PERFORMANCE SUMMARY")
    print(f"{'='*80}")

    for category in categories:
        queries = get_query_by_category(category)
        if not queries:
            continue

        ratings = []
        avg_keyword_coverage = []
        avg_relevance_ratio = []

        for query_def in queries:
            metrics = evaluator.evaluate_query(
                query=query_def["query"],
                expected_keywords=query_def["expected_keywords"],
                expected_topics=query_def["expected_topics"],
                top_k=10
            )

            ratings.append(metrics["rating"])
            avg_keyword_coverage.append(metrics["keyword_coverage"])
            avg_relevance_ratio.append(metrics["chunk_relevance_ratio"])

        # Calculate category stats
        good_count = ratings.count("GOOD")
        fair_count = ratings.count("FAIR")
        poor_count = ratings.count("POOR")
        avg_kw_cov = sum(avg_keyword_coverage) / len(avg_keyword_coverage) if avg_keyword_coverage else 0
        avg_rel_ratio = sum(avg_relevance_ratio) / len(avg_relevance_ratio) if avg_relevance_ratio else 0

        print(f"\n📁 {category.upper()} ({len(queries)} queries)")
        print(f"   Ratings: {good_count} GOOD, {fair_count} FAIR, {poor_count} POOR")
        print(f"   Avg Keyword Coverage: {avg_kw_cov:.1%}")
        print(f"   Avg Chunk Relevance: {avg_rel_ratio:.1%}")


def test_topk_comparison(evaluator):
    """Compare retrieval quality with different top_k values."""
    test_queries = DUCKLAKE_TEST_QUERIES[:3]  # Test with first 3 queries
    top_k_values = [5, 10, 20]

    print(f"\n{'='*80}")
    print(f"TOP-K COMPARISON")
    print(f"{'='*80}")

    for query_def in test_queries:
        print(f"\nQuery: {query_def['query']}")
        print(f"{'-'*80}")

        for k in top_k_values:
            metrics = evaluator.evaluate_query(
                query=query_def["query"],
                expected_keywords=query_def["expected_keywords"],
                expected_topics=query_def["expected_topics"],
                top_k=k
            )

            print(f"  k={k:2d}: {metrics['rating']:4s} | "
                  f"KeywordCov: {metrics['keyword_coverage']:5.1%} | "
                  f"ChunkRel: {metrics['chunk_relevance_ratio']:5.1%} | "
                  f"AvgDist: {metrics['avg_distance']:.3f}")


if __name__ == "__main__":
    """Run tests manually with detailed output."""
    import sys

    # Check if DuckLake document is ingested
    engine = create_rag_from_yaml(config_path="config/config.yaml")
    stats = engine.get_stats()

    print(f"\n{'='*80}")
    print(f"RAG ENGINE STATUS")
    print(f"{'='*80}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Embedding model: {stats['config']['embedding']['model']}")
    print(f"Vector store: {stats['config']['vector_store']['type']}")

    if stats['total_chunks'] == 0:
        print("\n⚠️  WARNING: No documents ingested!")
        print("Please run: python main.py ingest data/documents/ducklake.txt")
        sys.exit(1)

    # Run evaluation
    evaluator = RetrievalEvaluator(engine)

    print(f"\n{'='*80}")
    print(f"RUNNING DUCKLAKE RETRIEVAL EVALUATION")
    print(f"Testing {len(DUCKLAKE_TEST_QUERIES)} queries")
    print(f"{'='*80}")

    all_metrics = []
    for query_def in DUCKLAKE_TEST_QUERIES:
        metrics = evaluator.evaluate_query(
            query=query_def["query"],
            expected_keywords=query_def["expected_keywords"],
            expected_topics=query_def["expected_topics"],
            top_k=10
        )
        evaluator.print_evaluation(metrics)
        all_metrics.append(metrics)

    # Overall summary
    print(f"\n{'='*80}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*80}")

    ratings = [m["rating"] for m in all_metrics]
    good_count = ratings.count("GOOD")
    fair_count = ratings.count("FAIR")
    poor_count = ratings.count("POOR")

    avg_keyword_cov = sum(m["keyword_coverage"] for m in all_metrics) / len(all_metrics)
    avg_chunk_rel = sum(m["chunk_relevance_ratio"] for m in all_metrics) / len(all_metrics)
    avg_distance = sum(m["avg_distance"] for m in all_metrics) / len(all_metrics)

    print(f"\nRatings Distribution:")
    print(f"  GOOD: {good_count}/{len(all_metrics)} ({good_count/len(all_metrics):.1%})")
    print(f"  FAIR: {fair_count}/{len(all_metrics)} ({fair_count/len(all_metrics):.1%})")
    print(f"  POOR: {poor_count}/{len(all_metrics)} ({poor_count/len(all_metrics):.1%})")

    print(f"\nAverage Metrics:")
    print(f"  Keyword Coverage: {avg_keyword_cov:.1%}")
    print(f"  Chunk Relevance: {avg_chunk_rel:.1%}")
    print(f"  Distance: {avg_distance:.3f}")

    print(f"\n{'='*80}")
    print(f"EVALUATION COMPLETE")
    print(f"{'='*80}\n")
