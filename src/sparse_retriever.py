"""BM25 sparse retriever for keyword-based search."""

from typing import List, Dict, Any
import numpy as np


class BM25Retriever:
    """BM25 (Best Match 25) sparse retriever for keyword matching."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        try:
            from rank_bm25 import BM25Okapi
            self.BM25Okapi = BM25Okapi
        except ImportError:
            raise ImportError(
                "rank-bm25 is required for BM25Retriever. "
                "Install with: uv add rank-bm25"
            )

        self.k1 = k1
        self.b = b
        self.bm25 = None
        self.documents = []
        self.metadatas = []
        self.ids = []

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> None:
        """
        Add documents to the BM25 index.

        Args:
            ids: List of document IDs
            documents: List of document texts
            metadatas: Optional list of metadata dicts
        """
        self.ids.extend(ids)
        self.documents.extend(documents)

        if metadatas:
            self.metadatas.extend(metadatas)
        else:
            self.metadatas.extend([{} for _ in documents])

        # Tokenize documents
        tokenized_docs = [self._tokenize(doc) for doc in self.documents]

        # Build BM25 index
        self.bm25 = self.BM25Okapi(tokenized_docs)

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of results with scores and metadata
        """
        if not self.bm25:
            return []

        # Tokenize query
        tokenized_query = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Format results
        results = []
        for idx in top_indices:
            if idx < len(self.documents):
                results.append({
                    'id': self.ids[idx],
                    'document': self.documents[idx],
                    'metadata': self.metadatas[idx],
                    'score': float(scores[idx]),
                    'retrieval_type': 'sparse_bm25'
                })

        return results

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase + split on whitespace and punctuation.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Lowercase
        text = text.lower()

        # Replace common punctuation with spaces
        for char in '.,;:!?()[]{}""\'`-_/\\':
            text = text.replace(char, ' ')

        # Split and filter empty strings
        tokens = [t for t in text.split() if t]

        return tokens

    def clear(self) -> None:
        """Clear all documents from the index."""
        self.bm25 = None
        self.documents = []
        self.metadatas = []
        self.ids = []

    def count(self) -> int:
        """Return the number of documents in the index."""
        return len(self.documents)
