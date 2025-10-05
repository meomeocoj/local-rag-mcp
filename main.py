#!/usr/bin/env python3
"""CLI interface for the RAG engine."""

import argparse
import sys
from pathlib import Path
from src.engine import RAGEngine


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Minimal RAG Engine with Persistent Storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a document
  python main.py ingest path/to/document.md

  # Query without generation
  python main.py query "What is RAG?"

  # Generate an answer
  python main.py generate "What is RAG?"

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
        help='Ingest a markdown document into the RAG system'
    )
    ingest_parser.add_argument(
        'file_path',
        type=str,
        help='Path to the markdown file to ingest'
    )
    ingest_parser.add_argument(
        '--source-name',
        type=str,
        help='Optional name for the source (defaults to filename)'
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
        engine = RAGEngine(config_path=args.config)

        # Execute commands
        if args.command == 'ingest':
            file_path = Path(args.file_path)
            if not file_path.exists():
                print(f"Error: File not found: {args.file_path}", file=sys.stderr)
                sys.exit(1)

            num_chunks = engine.ingest_document(
                str(file_path),
                source_name=args.source_name
            )
            print(f"Successfully ingested {num_chunks} chunks from {file_path.name}")

        elif args.command == 'query':
            results = engine.query(args.query, top_k=args.top_k)

            if not results:
                print("No results found.")
            else:
                print(f"\nFound {len(results)} results:\n")
                for i, result in enumerate(results, 1):
                    print(f"[{i}] (distance: {result['distance']:.3f})")
                    print(f"Source: {result['metadata'].get('source', 'Unknown')}")
                    print(f"Content: {result['document'][:200]}...")
                    print()

        elif args.command == 'generate':
            if args.stream:
                print("\nGenerating answer (streaming):\n")
                for chunk in engine.generate_answer_stream(
                    args.query,
                    top_k=args.top_k,
                    system_prompt=args.system_prompt
                ):
                    print(chunk, end='', flush=True)
                print("\n")
            else:
                print("\nGenerating answer...\n")
                answer = engine.generate_answer(
                    args.query,
                    top_k=args.top_k,
                    system_prompt=args.system_prompt
                )
                print(answer)
                print()

        elif args.command == 'stats':
            stats = engine.get_stats()
            print("\n=== RAG Engine Statistics ===")
            print(f"Total chunks: {stats['total_chunks']}")
            print(f"Embedding dimension: {stats['embedding_dimension']}")
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
