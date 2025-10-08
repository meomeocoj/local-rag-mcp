#!/usr/bin/env python3
"""CLI interface for the RAG engine."""

import argparse
import sys
from pathlib import Path
from src.engine import create_rag_from_yaml


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Minimal RAG Engine with Persistent Storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest one or more documents (batch ingestion)
  python main.py ingest path/to/document.md
  python main.py ingest doc1.md doc2.md doc3.md

  # Query without generation (max 5 results, threshold 0.5)
  python main.py query "What is RAG?"

  # Generate an answer
  python main.py generate "What is RAG?"

  # Delete documents from index
  python main.py delete doc1.md doc2.md

  # Get statistics
  python main.py stats

  # Clear all data
  python main.py clear
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Ingest command
    ingest_parser = subparsers.add_parser(
        'ingest',
        help='Ingest markdown documents into the RAG system (supports multiple files)'
    )
    ingest_parser.add_argument(
        'file_paths',
        type=str,
        nargs='+',
        help='Path(s) to markdown file(s) to ingest'
    )

    # Query command
    query_parser = subparsers.add_parser(
        'query',
        help='Query the RAG system without generation'
    )
    query_parser.add_argument(
        'query',
        type=str,
        help='The search query'
    )
    query_parser.add_argument(
        '--top-k',
        type=int,
        help='Number of results to return'
    )
    query_parser.add_argument(
        '--document',
        type=str,
        help='Filter results to specific document (e.g., "duckdb.txt")'
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate an answer using RAG'
    )
    generate_parser.add_argument(
        'query',
        type=str,
        help='The user query'
    )
    generate_parser.add_argument(
        '--top-k',
        type=int,
        help='Number of chunks to retrieve'
    )
    generate_parser.add_argument(
        '--document',
        type=str,
        help='Filter results to specific document (e.g., "duckdb.txt")'
    )
    generate_parser.add_argument(
        '--stream',
        action='store_true',
        help='Stream the response'
    )
    generate_parser.add_argument(
        '--system-prompt',
        type=str,
        help='Optional system prompt'
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Get statistics about the RAG system'
    )

    # Delete command
    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete documents from the index'
    )
    delete_parser.add_argument(
        'document_ids',
        type=str,
        nargs='+',
        help='Document ID(s) or file path(s) to delete'
    )

    # Clear command
    clear_parser = subparsers.add_parser(
        'clear',
        help='Clear all data from the vector store'
    )
    clear_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Initialize the RAG engine
        engine = create_rag_from_yaml(config_path=args.config)

        # Execute commands
        if args.command == 'ingest':
            # Validate all files exist
            file_paths = [Path(fp) for fp in args.file_paths]
            for fp in file_paths:
                if not fp.exists():
                    print(f"Error: File not found: {fp}", file=sys.stderr)
                    sys.exit(1)

            # Use batch ingest (FR-014)
            result = engine.ingest([str(fp) for fp in file_paths])
            print(f"Successfully ingested {result['ingested_count']} file(s), {result['chunk_count']} chunks total")
            if result['failed_count'] > 0:
                print(f"Failed: {result['failed_count']} file(s)")
                for failure in result['failed_files']:
                    print(f"  - {failure}", file=sys.stderr)

        elif args.command == 'query':
            results = engine.query(
                args.query,
                top_k=args.top_k,
                document=args.document if hasattr(args, 'document') else None
            )

            # Show performance metrics
            perf = engine.get_performance_metrics()
            print(f"\nQuery time: {perf['last_query_time_ms']:.2f}ms")

            if not results:
                print("No results found (all results below 0.5 similarity threshold).")
            else:
                print(f"Found {len(results)} results (max 5, threshold >= 0.5):\n")
                for i, result in enumerate(results, 1):
                    content = result['document']
                    metadata = result.get('metadata', {})
                    distance = result.get('distance', 0)
                    # Convert distance to similarity score (cosine: similarity = 1 - distance)
                    score = 1 - distance if distance < 1 else 0

                    print(f"Rank {i} | Score: {score:.2f} | Source: {metadata.get('source', 'Unknown')}")

                    # Show header hierarchy if available
                    headers = metadata.get('headers', [])
                    if headers:
                        # Extract text from header dictionaries
                        header_texts = [h.get('text', str(h)) if isinstance(h, dict) else str(h) for h in headers]
                        section_path = " → ".join(header_texts)
                        print(f"Section: {section_path}")

                    # Show full content without truncation
                    print(f"\n{content}")
                    print("-" * 80)
                    print()

        elif args.command == 'delete':
            result = engine.delete(args.document_ids)
            print(f"Successfully deleted {result['deleted_count']} document(s)")
            if result['not_found_ids']:
                print(f"Not found: {len(result['not_found_ids'])} document(s)")
                for doc_id in result['not_found_ids']:
                    print(f"  - {doc_id}")

        elif args.command == 'generate':
            if args.stream:
                print("\nGenerating answer (streaming):\n")
                for chunk in engine.generate_answer_stream(
                    args.query,
                    top_k=args.top_k,
                    system_prompt=args.system_prompt,
                    document=args.document if hasattr(args, 'document') else None
                ):
                    print(chunk, end='', flush=True)
                print("\n")
            else:
                print("\nGenerating answer...\n")
                answer = engine.generate_answer(
                    args.query,
                    top_k=args.top_k,
                    system_prompt=args.system_prompt,
                    document=args.document if hasattr(args, 'document') else None
                )
                print(answer)
                print()

        elif args.command == 'stats':
            stats = engine.get_stats()
            perf = engine.get_performance_metrics()

            print("\n=== RAG Engine Statistics ===")
            print(f"Total chunks: {stats['total_chunks']}")
            print(f"Embedding dimension: {stats['embedding_dimension']}")

            print(f"\nPerformance Metrics:")
            print(f"  Query count: {perf['query_count']}")
            if perf['query_count'] > 0:
                print(f"  Average query time: {perf['avg_query_time_ms']:.2f}ms")
                print(f"  Last query time: {perf['last_query_time_ms']:.2f}ms")
                print(f"  Meets FR-011 (<500ms): {'✓ Yes' if perf['meets_fr011_requirement'] else '✗ No'}")

            print(f"\nConfiguration:")
            print(f"  Embedder: {stats['config']['embedding']['provider']}")
            print(f"  Model: {stats['config']['embedding']['model']}")
            print(f"  Vector Store: {stats['config']['vector_store']['type']}")
            print(f"  Generator: {stats['config']['generation']['model']}")
            print()

        elif args.command == 'clear':
            if not args.confirm:
                response = input("Are you sure you want to clear all data? (yes/no): ")
                if response.lower() != 'yes':
                    print("Cancelled.")
                    sys.exit(0)

            engine.clear()
            print("All data cleared successfully.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
