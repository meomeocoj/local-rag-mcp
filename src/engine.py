"""Main RAG engine orchestrator."""

import os
from typing import List, Dict, Any, Optional, Iterator
import yaml
from pathlib import Path

from src.chunker import MarkdownChunker
from src.embedder import EmbedderFactory, EmbedderInterface
from src.vector_store import ChromaDBStore, VectorStoreInterface
from src.retriever import Retriever
from src.generator import Generator


class RAGEngine:
    """Main RAG engine that orchestrates all components."""

    def __init__(
        self,
        chunker: MarkdownChunker,
        embedder: EmbedderInterface,
        vector_store: VectorStoreInterface,
        generator: Generator,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the RAG engine with injected dependencies.

        Args:
            chunker: Chunker instance for splitting documents
            embedder: Embedder instance for generating embeddings
            vector_store: Vector store instance for storage and retrieval
            generator: Generator instance for answer generation
            config: Optional configuration dictionary
        """
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.retriever = Retriever(embedder, vector_store)
        self.generator = generator
        self.config = config or {}

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

        return len(chunks)

    def query(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the RAG system without generation.

        Args:
            query: The search query
            top_k: Number of results (defaults to config value)

        Returns:
            Retrieved chunks with metadata
        """
        if top_k is None:
            top_k = self.config.get('generation', {}).get('top_k', 3)

        return self.retriever.retrieve(query, top_k=top_k)

    def generate_answer(
        self,
        query: str,
        top_k: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate an answer for a query using RAG.

        Args:
            query: The user query
            top_k: Number of chunks to retrieve
            system_prompt: Optional system prompt

        Returns:
            Generated answer
        """
        # Retrieve relevant chunks
        context = self.query(query, top_k=top_k)

        # Generate answer
        return self.generator.generate(query, context, system_prompt)

    def generate_answer_stream(
        self,
        query: str,
        top_k: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        """
        Generate an answer with streaming.

        Args:
            query: The user query
            top_k: Number of chunks to retrieve
            system_prompt: Optional system prompt

        Yields:
            Chunks of the generated answer
        """
        # Retrieve relevant chunks
        context = self.query(query, top_k=top_k)

        # Generate answer with streaming
        yield from self.generator.generate_stream(query, context, system_prompt)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        return {
            'total_chunks': self.vector_store.count(),
            'embedding_dimension': self.embedder.get_dimension(),
            'config': self.config
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
        overlap=chunking_config.get('overlap', 50)
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

    # Create and return RAG engine
    return RAGEngine(
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        generator=generator,
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
