#!/usr/bin/env python3
"""Performance benchmark script for RAG engine.

Tests FR-011: Query performance requirement (<500ms for 1000 documents).
"""

import time
import statistics
from pathlib import Path
from src.engine import create_rag_from_yaml


def create_test_documents(num_docs: int, output_dir: Path) -> list[str]:
    """Create test markdown documents for benchmarking."""
    output_dir.mkdir(parents=True, exist_ok=True)
    file_paths = []

    for i in range(num_docs):
        content = f"""# Test Document {i}

## Overview
This is test document number {i} created for performance benchmarking.

## Section A
Content for section A in document {i}. This section contains information
about topic A which is relevant for retrieval testing.

## Section B
Content for section B in document {i}. This section discusses topic B
and provides additional context for semantic search.

## Section C
Final section with code examples:

```python
def function_{i}():
    return "Document {i}"
```

## Conclusion
This concludes document {i} with {100 + i} tokens of content.
"""
        file_path = output_dir / f"doc_{i:04d}.md"
        file_path.write_text(content)
        file_paths.append(str(file_path))

    return file_paths


def benchmark_query_performance(engine, queries: list[str], iterations: int = 10):
    """Benchmark query performance with multiple iterations."""
    results = {
        'query_times': [],
        'iterations': iterations,
        'num_queries': len(queries)
    }

    print(f"\nRunning {iterations} iterations of {len(queries)} queries...")

    for iteration in range(iterations):
        for query in queries:
            start = time.time()
            engine.query(query)
            elapsed_ms = (time.time() - start) * 1000
            results['query_times'].append(elapsed_ms)

    # Calculate statistics
    results['mean_ms'] = statistics.mean(results['query_times'])
    results['median_ms'] = statistics.median(results['query_times'])
    results['stdev_ms'] = statistics.stdev(results['query_times']) if len(results['query_times']) > 1 else 0
    results['min_ms'] = min(results['query_times'])
    results['max_ms'] = max(results['query_times'])
    results['p95_ms'] = statistics.quantiles(results['query_times'], n=20)[18]  # 95th percentile
    results['p99_ms'] = statistics.quantiles(results['query_times'], n=100)[98]  # 99th percentile

    return results


def main():
    """Run performance benchmarks."""
    print("=" * 80)
    print("RAG Engine Performance Benchmark")
    print("=" * 80)

    # Configuration
    num_docs = 1000
    benchmark_dir = Path("./data/benchmark_docs")

    print(f"\nConfiguration:")
    print(f"  Target documents: {num_docs}")
    print(f"  FR-011 requirement: <500ms per query")

    # Create test documents
    print(f"\nCreating {num_docs} test documents...")
    file_paths = create_test_documents(num_docs, benchmark_dir)
    print(f"  Created {len(file_paths)} documents")

    # Initialize engine
    print("\nInitializing RAG engine...")
    engine = create_rag_from_yaml()

    # Clear existing data
    print("  Clearing existing data...")
    engine.clear()

    # Ingest documents
    print(f"  Ingesting {num_docs} documents...")
    start_ingest = time.time()
    result = engine.ingest(file_paths)
    ingest_time = time.time() - start_ingest

    print(f"  Ingested {result['ingested_count']} documents")
    print(f"  Created {result['chunk_count']} chunks")
    print(f"  Ingestion time: {ingest_time:.2f}s")
    print(f"  Throughput: {result['ingested_count'] / ingest_time:.1f} docs/s")

    # Test queries
    queries = [
        "What is topic A?",
        "Tell me about section B",
        "Show me code examples",
        "Overview of the documents",
        "Conclusion and summary"
    ]

    # Run benchmark
    print("\n" + "=" * 80)
    print("Query Performance Benchmark")
    print("=" * 80)

    results = benchmark_query_performance(engine, queries, iterations=10)

    # Display results
    print(f"\nResults ({results['iterations']} iterations × {results['num_queries']} queries = {len(results['query_times'])} total queries):")
    print(f"  Mean:     {results['mean_ms']:>8.2f} ms")
    print(f"  Median:   {results['median_ms']:>8.2f} ms")
    print(f"  Std Dev:  {results['stdev_ms']:>8.2f} ms")
    print(f"  Min:      {results['min_ms']:>8.2f} ms")
    print(f"  Max:      {results['max_ms']:>8.2f} ms")
    print(f"  P95:      {results['p95_ms']:>8.2f} ms")
    print(f"  P99:      {results['p99_ms']:>8.2f} ms")

    # FR-011 compliance check
    print("\n" + "=" * 80)
    print("FR-011 Compliance Check (<500ms requirement)")
    print("=" * 80)

    fr011_compliant = results['p95_ms'] < 500
    print(f"  P95 latency: {results['p95_ms']:.2f}ms")
    print(f"  Requirement: <500ms")
    print(f"  Status: {'✓ PASS' if fr011_compliant else '✗ FAIL'}")

    if fr011_compliant:
        headroom = 500 - results['p95_ms']
        print(f"  Headroom: {headroom:.2f}ms ({headroom/500*100:.1f}%)")

    # Get engine performance metrics
    print("\n" + "=" * 80)
    print("Engine Performance Metrics")
    print("=" * 80)

    perf = engine.get_performance_metrics()
    print(f"  Total queries: {perf['query_count']}")
    print(f"  Avg query time: {perf['avg_query_time_ms']:.2f}ms")
    print(f"  Last query time: {perf['last_query_time_ms']:.2f}ms")
    print(f"  FR-011 compliant: {'✓ Yes' if perf['meets_fr011_requirement'] else '✗ No'}")

    # Cleanup
    print("\n" + "=" * 80)
    print("Cleanup")
    print("=" * 80)
    print("  Clearing benchmark data from vector store...")
    engine.clear()
    print("  Removing benchmark documents...")
    for fp in file_paths:
        Path(fp).unlink()
    benchmark_dir.rmdir()
    print("  ✓ Cleanup complete")

    print("\n" + "=" * 80)
    print("Benchmark Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
