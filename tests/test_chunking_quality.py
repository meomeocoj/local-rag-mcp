"""Test chunking quality for DuckLake documentation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chunker import MarkdownChunker


def analyze_chunk_quality(chunks, strategy_name):
    """Analyze quality metrics for chunks."""
    print(f"\n{'='*80}")
    print(f"CHUNKING STRATEGY: {strategy_name}")
    print(f"{'='*80}")

    total_chunks = len(chunks)

    # Quality metrics
    broken_start_count = 0
    broken_end_count = 0
    duplicate_text_count = 0
    missing_context_count = 0

    chunk_sizes = [len(c.text) for c in chunks]
    avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0

    print(f"\n📊 BASIC STATS:")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Avg chunk size: {avg_size:.0f} chars")
    print(f"  Min size: {min(chunk_sizes)}")
    print(f"  Max size: {max(chunk_sizes)}")

    # Sample first 5 chunks for quality
    print(f"\n🔍 QUALITY INSPECTION (first 5 chunks):")

    for i, chunk in enumerate(chunks[:5]):
        print(f"\n  --- CHUNK {i} ---")
        print(f"  Length: {len(chunk.text)} chars")
        print(f"  Headers: {chunk.metadata.get('headers', [])}")

        # Check for broken starts (lowercase start, no header)
        first_line = chunk.text.strip().split('\n')[0]
        if not first_line.startswith('#') and len(first_line) > 0 and first_line[0].islower():
            broken_start_count += 1
            print(f"  ⚠️  BROKEN START (lowercase): '{first_line[:50]}'")
        else:
            print(f"  ✓ Good start: '{first_line[:50]}'")

        # Check for broken ends (mid-sentence)
        last_line = chunk.text.strip().split('\n')[-1]
        if last_line and not last_line.endswith(('.', '!', '?', '```', '|', ')')):
            broken_end_count += 1
            print(f"  ⚠️  BROKEN END: '{last_line[-50:]}'")
        else:
            print(f"  ✓ Good end")

        # Check for duplicate text (same content at start and end)
        if len(chunk.text) > 400:
            start_snippet = chunk.text[:200]
            end_snippet = chunk.text[-200:]
            if start_snippet in end_snippet or end_snippet in start_snippet:
                duplicate_text_count += 1
                print(f"  ⚠️  DUPLICATE TEXT detected")

        # Check for missing context (no headers extracted)
        if not chunk.metadata.get('headers'):
            missing_context_count += 1
            print(f"  ⚠️  NO HEADERS (missing context)")

        # Show preview
        preview = chunk.text[:150].replace('\n', ' ')
        print(f"  Preview: {preview}...")

    print(f"\n📋 QUALITY SUMMARY:")
    print(f"  Broken starts: {broken_start_count}/5")
    print(f"  Broken ends: {broken_end_count}/5")
    print(f"  Duplicate text: {duplicate_text_count}/5")
    print(f"  Missing context: {missing_context_count}/5")

    quality_score = (5 - broken_start_count - broken_end_count - duplicate_text_count) / 5 * 100
    print(f"\n  QUALITY SCORE: {quality_score:.0f}%")

    return {
        'strategy': strategy_name,
        'total_chunks': total_chunks,
        'avg_size': avg_size,
        'broken_starts': broken_start_count,
        'broken_ends': broken_end_count,
        'duplicate_text': duplicate_text_count,
        'missing_context': missing_context_count,
        'quality_score': quality_score
    }


def test_chunking_strategies():
    """Compare different chunking strategies."""
    doc = Path('data/documents/ducklake.txt').read_text()

    strategies = [
        {
            'name': 'Current: Recursive 4096, overlap 400',
            'chunker': MarkdownChunker(
                max_chunk_size=4096,
                overlap=400,
                strategy='recursive'
            )
        },
        {
            'name': 'Recursive 4096, NO overlap',
            'chunker': MarkdownChunker(
                max_chunk_size=4096,
                overlap=0,
                strategy='recursive'
            )
        },
        {
            'name': 'Recursive 2048, overlap 200',
            'chunker': MarkdownChunker(
                max_chunk_size=2048,
                overlap=200,
                strategy='recursive'
            )
        },
        {
            'name': 'Semantic 4096, overlap 400',
            'chunker': MarkdownChunker(
                max_chunk_size=4096,
                overlap=400,
                strategy='semantic'
            )
        },
        {
            'name': 'Headers (original) 4096, overlap 400',
            'chunker': MarkdownChunker(
                max_chunk_size=4096,
                overlap=400,
                strategy='headers'
            )
        }
    ]

    results = []

    for strategy in strategies:
        chunks = strategy['chunker'].chunk_document(doc, source='ducklake.txt')
        metrics = analyze_chunk_quality(chunks, strategy['name'])
        results.append(metrics)

    # Comparison summary
    print(f"\n{'='*80}")
    print(f"STRATEGY COMPARISON")
    print(f"{'='*80}")

    print(f"\n{'Strategy':<45} {'Chunks':>8} {'Avg Size':>10} {'Quality':>10}")
    print(f"{'-'*80}")

    for r in results:
        print(f"{r['strategy']:<45} {r['total_chunks']:>8} {r['avg_size']:>10.0f} {r['quality_score']:>9.0f}%")

    # Best strategy
    best = max(results, key=lambda x: x['quality_score'])
    print(f"\n🏆 BEST QUALITY: {best['strategy']} ({best['quality_score']:.0f}%)")

    # Most chunks (better granularity)
    most_chunks = max(results, key=lambda x: x['total_chunks'])
    print(f"📊 MOST GRANULAR: {most_chunks['strategy']} ({most_chunks['total_chunks']} chunks)")


if __name__ == '__main__':
    test_chunking_strategies()
