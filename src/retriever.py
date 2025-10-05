"""Retrieval module for searching and retrieving relevant chunks."""

from typing import List, Dict, Any
from src.embedder import EmbedderInterface
from src.vector_store import VectorStoreInterface


class Retriever:
    """Retrieves relevant chunks based on query embedding."""

    def __init__(
        self,
        embedder: EmbedderInterface,
        vector_store: VectorStoreInterface
    ):
        """
        Initialize the retriever.

        Args:
            embedder: Embedder instance for encoding queries
            vector_store: Vector store instance for searching
        """
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            List of results with documents and metadata
        """
        # Embed the query
        query_embedding = self.embedder.embed_text(query)

        # Search the vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        return results

    def retrieve_with_scores(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with similarity scores.

        Args:
            query: The search query
            top_k: Number of results to return
            score_threshold: Optional minimum similarity score

        Returns:
            List of results with documents, metadata, and scores
        """
        results = self.retrieve(query, top_k)

        # Filter by score threshold if specified
        if score_threshold is not None:
            # ChromaDB returns distances, convert to similarity scores
            # For cosine distance, similarity = 1 - distance
            filtered_results = []
            for result in results:
                similarity = 1 - result['distance']
                if similarity >= score_threshold:
                    result['similarity'] = similarity
                    filtered_results.append(result)
            return filtered_results

        # Add similarity scores to all results
        for result in results:
            result['similarity'] = 1 - result['distance']

        return results

    def retrieve_batch(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Retrieve results for multiple queries.

        Args:
            queries: List of search queries
            top_k: Number of results per query

        Returns:
            List of result lists, one per query
        """
        return [self.retrieve(query, top_k) for query in queries]
