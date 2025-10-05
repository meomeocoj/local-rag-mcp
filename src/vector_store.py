"""Vector store interface and ChromaDB implementation."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class VectorStoreInterface(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add(
        self,
        ids: List[str],
        embeddings: List[np.ndarray],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add vectors to the store."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        pass

    @abstractmethod
    def persist(self) -> None:
        """Persist the store to disk."""
        pass

    @abstractmethod
    def load(self) -> None:
        """Load the store from disk."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return the number of vectors in the store."""
        pass


class ChromaDBStore(VectorStoreInterface):
    """ChromaDB vector store implementation."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "documents",
        distance_metric: str = "cosine"
    ):
        """
        Initialize ChromaDB store.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
            distance_metric: Distance metric ('cosine', 'l2', or 'ip')
        """
        import chromadb
        from chromadb.config import Settings

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Map distance metrics to ChromaDB space names
        metric_map = {
            "cosine": "cosine",
            "l2": "l2",
            "ip": "ip"
        }
        self.distance_metric = metric_map.get(distance_metric, "cosine")

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": self.distance_metric}
        )

    def add(
        self,
        ids: List[str],
        embeddings: List[np.ndarray],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add vectors to the store."""
        # Convert numpy arrays to lists for ChromaDB
        embeddings_list = [emb.tolist() for emb in embeddings]

        # Sanitize metadata - ChromaDB has restrictions on metadata values
        if metadatas:
            sanitized_metadatas = []
            for metadata in metadatas:
                sanitized = {}
                for key, value in metadata.items():
                    # Convert complex types to strings
                    if isinstance(value, (list, dict)):
                        sanitized[key] = str(value)
                    elif value is None:
                        sanitized[key] = ""
                    else:
                        sanitized[key] = value
                sanitized_metadatas.append(sanitized)
        else:
            sanitized_metadatas = None

        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=documents,
            metadatas=sanitized_metadatas
        )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })

        return formatted_results

    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        self.collection.delete(ids=ids)

    def persist(self) -> None:
        """Persist the store to disk."""
        # ChromaDB with PersistentClient automatically persists
        # This method is kept for interface compatibility
        pass

    def load(self) -> None:
        """Load the store from disk."""
        # ChromaDB automatically loads on initialization
        # This method is kept for interface compatibility
        pass

    def count(self) -> int:
        """Return the number of vectors in the store."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all vectors from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": self.distance_metric}
        )
