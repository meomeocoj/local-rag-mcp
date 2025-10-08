"""Main RAG engine orchestrator."""

import os
import time
from typing import List, Dict, Any, Optional, Iterator
import yaml
from pathlib import Path

from src.chunker import MarkdownChunker
from src.embedder import EmbedderFactory, EmbedderInterface
from src.vector_store import ChromaDBStore, VectorStoreInterface
from src.retriever import Retriever, HybridRetriever
from src.sparse_retriever import BM25Retriever
from src.generator import Generator


class RAGEngine:
    """Main RAG engine that orchestrates all components."""

    def __init__(
        self,
        chunker: MarkdownChunker,
        embedder: EmbedderInterface,
        vector_store: VectorStoreInterface,
        generator: Generator,
        sparse_retriever: Optional[BM25Retriever] = None,
        use_hybrid: bool = False,
        hybrid_alpha: float = 0.5,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the RAG engine with injected dependencies.

        Args:
            chunker: Chunker instance for splitting documents
            embedder: Embedder instance for generating embeddings
            vector_store: Vector store instance for storage and retrieval
            generator: Generator instance for answer generation
            sparse_retriever: Optional BM25 retriever for hybrid search
            use_hybrid: Whether to use hybrid retrieval (default: False)
            hybrid_alpha: Weight for dense vs sparse in hybrid (default: 0.5)
            config: Optional configuration dictionary
        """
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.sparse_retriever = sparse_retriever
        self.generator = generator
        self.config = config or {}

        # Performance metrics
        self.metrics = {
            'query_count': 0,
            'total_query_time': 0.0,
            'avg_query_time': 0.0,
            'last_query_time': 0.0
        }

        # Initialize retriever based on configuration
        if use_hybrid and sparse_retriever:
            self.retriever = HybridRetriever(
                embedder,
                vector_store,
                sparse_retriever,
                alpha=hybrid_alpha
            )
        else:
            self.retriever = Retriever(embedder, vector_store)

    def ingest(
        self,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Batch ingest multiple markdown documents into the RAG system.

        Implements FR-014: Batch ingestion support.

        Args:
            file_paths: List of paths to markdown files

        Returns:
            Dictionary with:
                - ingested_count: Number of successfully ingested files
                - failed_count: Number of failed files
                - chunk_count: Total chunks created
                - failed_files: List of file paths that failed
                - document_ids: List of document IDs for successfully ingested files
        """
        ingested_count = 0
        failed_count = 0
        chunk_count = 0
        failed_files = []
        document_ids = []

        for file_path in file_paths:
            try:
                chunks = self.ingest_document(file_path)
                ingested_count += 1
                chunk_count += chunks
                document_ids.append(file_path)
            except Exception as e:
                failed_count += 1
                failed_files.append(f"{file_path}: {str(e)}")

        return {
            'ingested_count': ingested_count,
            'failed_count': failed_count,
            'chunk_count': chunk_count,
            'failed_files': failed_files,
            'document_ids': document_ids
        }

    def ingest_document(
        self,
        file_path: str,
        source_name: Optional[str] = None
    ) -> int:
        """
        Ingest a markdown document into the RAG system.

        Args:
            file_path: Path to the markdown file
            source_name: Optional name for the source (defaults to filename)

        Returns:
            Number of chunks created
        """
        # Read document
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Use filename as source if not provided
        if source_name is None:
            source_name = Path(file_path).name

        # Chunk the document
        chunks = self.chunker.chunk_document(text, source=source_name)

        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_batch(chunk_texts)

        # Handle case where some embeddings failed
        if len(embeddings) < len(chunks):
            print(f"[WARNING] Only {len(embeddings)}/{len(chunks)} chunks were successfully embedded")
            print(f"[WARNING] Skipping {len(chunks) - len(embeddings)} failed chunks")

            # Only keep chunks that were successfully embedded
            # This is a limitation - we're truncating to match embedding count
            chunks = chunks[:len(embeddings)]
            chunk_texts = chunk_texts[:len(embeddings)]

        # Create unique IDs
        ids = [f"{source_name}_{i}" for i in range(len(chunks))]

        # Extract metadata
        metadatas = [chunk.metadata for chunk in chunks]

        # Add to vector store
        self.vector_store.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas
        )

        # Add to sparse retriever if using hybrid search
        if self.sparse_retriever:
            self.sparse_retriever.add_documents(
                ids=ids,
                documents=chunk_texts,
                metadatas=metadatas
            )

        return len(chunks)

    def ingest_text(
        self,
        text: str,
        source_name: str = "text_input"
    ) -> int:
        """
        Ingest raw text into the RAG system.

        Args:
            text: The text to ingest
            source_name: Name for the source

        Returns:
            Number of chunks created
        """
        # Chunk the text
        chunks = self.chunker.chunk_document(text, source=source_name)

        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_batch(chunk_texts)

        # Create unique IDs
        ids = [f"{source_name}_{i}" for i in range(len(chunks))]

        # Extract metadata
        metadatas = [chunk.metadata for chunk in chunks]

        # Add to vector store
        self.vector_store.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas
        )

        # Add to sparse retriever if using hybrid search
        if self.sparse_retriever:
            self.sparse_retriever.add_documents(
                ids=ids,
                documents=chunk_texts,
                metadatas=metadatas
            )

        return len(chunks)

    def delete(
        self,
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Manually delete documents from the index.

        Implements FR-015: Manual document deletion.

        Args:
            document_ids: List of document IDs or file paths to delete

        Returns:
            Dictionary with:
                - deleted_count: Number of documents removed
                - deleted_ids: List of IDs successfully deleted
                - not_found_ids: List of IDs not in index
        """
        deleted_ids = []
        not_found_ids = []

        for doc_id in document_ids:
            try:
                # Extract source name from doc_id
                if '/' in doc_id or '\\' in doc_id:
                    source_name = Path(doc_id).name
                else:
                    source_name = doc_id

                # Check if document exists by trying to query for first chunk
                # Get all chunks from vector store to see if any match this source
                initial_count = self.vector_store.count()

                # Collect chunk IDs to delete
                chunk_ids_to_delete = []
                for i in range(1000):  # Assume max 1000 chunks per doc
                    chunk_id = f"{source_name}_{i}"
                    chunk_ids_to_delete.append(chunk_id)

                # Try to delete all potential chunks
                if chunk_ids_to_delete:
                    self.vector_store.delete(chunk_ids_to_delete)

                # Check if anything was actually deleted
                final_count = self.vector_store.count()

                if final_count < initial_count:
                    deleted_ids.append(doc_id)
                else:
                    not_found_ids.append(doc_id)

            except Exception:
                not_found_ids.append(doc_id)

        return {
            'deleted_count': len(deleted_ids),
            'deleted_ids': deleted_ids,
            'not_found_ids': not_found_ids
        }

    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the RAG system without generation.

        Implements FR-012 (max 5 results) and FR-013 (0.5 threshold).

        Args:
            query: The search query
            top_k: Number of results (default: 5, enforced as max)
            score_threshold: Minimum similarity score (default: 0.5)

        Returns:
            Retrieved chunks with metadata, filtered and limited
        """
        # Start timing (FR-011: <500ms requirement)
        start_time = time.time()

        # FR-012: Enforce max 5 results
        if top_k is None:
            top_k = 5
        else:
            top_k = min(top_k, 5)  # Never exceed 5

        # FR-013: Enforce 0.5 similarity threshold
        if score_threshold is None:
            score_threshold = 0.5

        # Use the retriever's method with score filtering
        # Both Retriever and HybridRetriever have retrieve() method
        results = self.retriever.retrieve(query, top_k=top_k)

        # Apply threshold filtering
        filtered_results = []
        for result in results:
            distance = result.get('distance', 0)
            score = 1 - distance  # Convert distance to similarity
            if score >= score_threshold:
                filtered_results.append(result)

        # Update metrics
        elapsed = time.time() - start_time
        self.metrics['query_count'] += 1
        self.metrics['total_query_time'] += elapsed
        self.metrics['avg_query_time'] = self.metrics['total_query_time'] / self.metrics['query_count']
        self.metrics['last_query_time'] = elapsed

        return filtered_results

    def generate_answer(
        self,
        query: str,
        top_k: Optional[int] = None,
        system_prompt: Optional[str] = None,
        document: str = None
    ) -> str:
        """
        Generate an answer for a query using RAG.

        Args:
            query: The user query
            top_k: Number of chunks to retrieve
            system_prompt: Optional system prompt
            document: Optional document name to filter results

        Returns:
            Generated answer
        """
        # Retrieve relevant chunks
        context = self.query(query, top_k=top_k, document=document)

        # Generate answer
        return self.generator.generate(query, context, system_prompt)

    def generate_answer_stream(
        self,
        query: str,
        top_k: Optional[int] = None,
        system_prompt: Optional[str] = None,
        document: str = None
    ) -> Iterator[str]:
        """
        Generate an answer with streaming.

        Args:
            query: The user query
            top_k: Number of chunks to retrieve
            system_prompt: Optional system prompt
            document: Optional document name to filter results

        Yields:
            Chunks of the generated answer
        """
        # Retrieve relevant chunks
        context = self.query(query, top_k=top_k, document=document)

        # Generate answer with streaming
        yield from self.generator.generate_stream(query, context, system_prompt)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        return {
            'total_chunks': self.vector_store.count(),
            'embedding_dimension': self.embedder.get_dimension(),
            'performance': self.metrics,
            'config': self.config
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics.

        Returns:
            Dictionary with query performance stats
        """
        return {
            'query_count': self.metrics['query_count'],
            'total_query_time_ms': self.metrics['total_query_time'] * 1000,
            'avg_query_time_ms': self.metrics['avg_query_time'] * 1000,
            'last_query_time_ms': self.metrics['last_query_time'] * 1000,
            'meets_fr011_requirement': self.metrics['avg_query_time'] < 0.5  # <500ms
        }

    def clear(self) -> None:
        """Clear all data from the vector store."""
        self.vector_store.clear()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable substitution.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    # Handle environment variable substitution
    with open(config_path, 'r') as f:
        config_text = f.read()

    # Simple environment variable substitution
    import re
    env_pattern = re.compile(r'\$\{(\w+)\}')
    config_text = env_pattern.sub(
        lambda m: os.environ.get(m.group(1), m.group(0)),
        config_text
    )

    return yaml.safe_load(config_text)


def create_rag_from_config(config: Dict[str, Any]) -> RAGEngine:
    """
    Create a RAG engine instance from a configuration dictionary.

    Args:
        config: Configuration dictionary with chunking, embedding, vector_store, and generation sections

    Returns:
        Configured RAGEngine instance
    """
    # Initialize chunker
    chunking_config = config.get('chunking', {})
    chunker = MarkdownChunker(
        max_chunk_size=chunking_config.get('max_chunk_size', 512),
        overlap=chunking_config.get('overlap', 50),
        strategy=chunking_config.get('strategy', 'headers'),
        max_tokens_per_chunk=chunking_config.get('max_tokens_per_chunk', 5000)
    )

    # Initialize embedder
    embedding_config = config.get('embedding', {})
    provider = embedding_config.get('provider', 'sentence_transformers')
    model = embedding_config.get('model', 'all-MiniLM-L6-v2')

    kwargs = {}
    if 'api_key' in embedding_config:
        kwargs['api_key'] = embedding_config['api_key']
    if 'endpoint' in embedding_config:
        kwargs['endpoint'] = embedding_config['endpoint']
    if 'batch_size' in embedding_config:
        kwargs['batch_size'] = embedding_config['batch_size']

    embedder = EmbedderFactory.create_embedder(provider, model, **kwargs)

    # Initialize vector store
    vs_config = config.get('vector_store', {})
    vector_store = ChromaDBStore(
        persist_directory=vs_config.get('persist_directory', './data/chroma_db'),
        collection_name=vs_config.get('collection_name', 'documents'),
        distance_metric=vs_config.get('distance_metric', 'cosine')
    )

    # Initialize generator
    gen_config = config.get('generation', {})
    generator = Generator(
        provider=gen_config.get('provider', 'openai'),
        model=gen_config.get('model', 'gpt-3.5-turbo'),
        temperature=gen_config.get('temperature', 0.7),
        max_tokens=gen_config.get('max_tokens', 512)
    )

    # Initialize sparse retriever if using hybrid search
    retrieval_config = config.get('retrieval', {})
    use_hybrid = retrieval_config.get('type', 'dense') == 'hybrid'
    sparse_retriever = None

    if use_hybrid:
        sparse_retriever = BM25Retriever(
            k1=retrieval_config.get('bm25_k1', 1.5),
            b=retrieval_config.get('bm25_b', 0.75)
        )

    # Create and return RAG engine
    return RAGEngine(
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        generator=generator,
        sparse_retriever=sparse_retriever,
        use_hybrid=use_hybrid,
        hybrid_alpha=retrieval_config.get('alpha', 0.5),
        config=config
    )


def create_rag_from_yaml(config_path: str = "config/config.yaml") -> RAGEngine:
    """
    Create a RAG engine instance from a YAML configuration file.

    This is the main utility function for creating a RAG engine with all dependencies
    properly initialized from a YAML configuration file.

    Args:
        config_path: Path to YAML configuration file (default: "config/config.yaml")

    Returns:
        Configured RAGEngine instance with all dependencies injected

    Example:
        >>> engine = create_rag_from_yaml("config/config.yaml")
        >>> engine.ingest_document("docs/readme.md")
        >>> answer = engine.generate_answer("What is RAG?")
    """
    config = load_config(config_path)
    return create_rag_from_config(config)
