"""Retrieval module for searching and retrieving relevant chunks."""

from typing import List, Dict, Any, Optional
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
        top_k: int = 5,
        document: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: The search query
            top_k: Number of results to return
            document: Optional document name to filter results

        Returns:
            List of results with documents and metadata
        """
        # Embed the query
        query_embedding = self.embedder.embed_text(query)

        # Build metadata filter if document specified
        where = {"source": document} if document else None

        # Search the vector store
        results = self.vector_store.search(query_embedding, top_k=top_k, where=where)

        return results

    def retrieve_with_scores(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = None,
        document: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with similarity scores.

        Args:
            query: The search query
            document: Optional document name to filter results
            top_k: Number of results to return
            score_threshold: Optional minimum similarity score

        Returns:
            List of results with documents, metadata, and scores
        """
        results = self.retrieve(query, top_k, document=document)

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


class HybridRetriever:
    """Hybrid retriever combining dense (vector) and sparse (BM25) search."""

    def __init__(
        self,
        embedder: EmbedderInterface,
        vector_store: VectorStoreInterface,
        sparse_retriever,  # BM25Retriever
        alpha: float = 0.5
    ):
        """
        Initialize hybrid retriever.

        Args:
            embedder: Embedder for dense retrieval
            vector_store: Vector store for dense retrieval
            sparse_retriever: BM25 retriever for sparse retrieval
            alpha: Weight for combining scores (0=sparse only, 1=dense only)
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.sparse_retriever = sparse_retriever
        self.alpha = alpha

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        initial_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve using hybrid search (dense + sparse).

        Args:
            query: Search query
            top_k: Number of final results
            initial_k: Number of candidates from each method (default: 2*top_k)

        Returns:
            Combined and reranked results
        """
        if initial_k is None:
            initial_k = top_k * 2

        # Get dense (vector) results
        query_embedding = self.embedder.embed_text(query)
        dense_results = self.vector_store.search(query_embedding, top_k=initial_k)

        # Get sparse (BM25) results
        sparse_results = self.sparse_retriever.search(query, top_k=initial_k)

        # Combine using Reciprocal Rank Fusion (RRF)
        combined = self._reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            k=60  # RRF parameter
        )

        # Return top-k
        return combined[:top_k]

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).
        RRF formula: score = sum(1 / (k + rank))

        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse retrieval
            k: RRF parameter (default: 60)

        Returns:
            Combined and sorted results
        """
        # Create score dictionary by document ID
        doc_scores = {}
        doc_data = {}

        # Process dense results (use distance as rank proxy)
        for rank, result in enumerate(dense_results, 1):
            doc_id = result.get('id', result['document'][:50])  # Use doc start as ID if missing
            rrf_score = 1.0 / (k + rank)

            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + self.alpha * rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Process sparse results
        for rank, result in enumerate(sparse_results, 1):
            doc_id = result.get('id', result['document'][:50])
            rrf_score = 1.0 / (k + rank)

            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + (1 - self.alpha) * rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Sort by combined score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Format results
        combined_results = []
        for doc_id, score in sorted_docs:
            result = doc_data[doc_id].copy()
            result['hybrid_score'] = score
            result['retrieval_type'] = 'hybrid'
            combined_results.append(result)

        return combined_results
