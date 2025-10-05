"""Embedding interface and implementations."""

from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np


class EmbedderInterface(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Embed a batch of text strings."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the dimension of embeddings."""
        pass


class SentenceTransformerEmbedder(EmbedderInterface):
    """Sentence Transformers embedder using local models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the sentence transformer embedder.

        Args:
            model_name: Name of the sentence-transformers model
        """
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Embed a batch of text strings."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [embeddings[i] for i in range(len(embeddings))]

    def get_dimension(self) -> int:
        """Return the dimension of embeddings."""
        return self.dimension


class OpenAIEmbedder(EmbedderInterface):
    """OpenAI embedder using API."""

    def __init__(
        self,
        model_name: str = "text-embedding-ada-002",
        api_key: str = None,
        endpoint: str = None
    ):
        """
        Initialize the OpenAI embedder.

        Args:
            model_name: Name of the OpenAI embedding model
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            endpoint: Optional custom endpoint
        """
        from openai import OpenAI

        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=endpoint)

        # Dimension mapping for known models
        self.dimension_map = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        self.dimension = self.dimension_map.get(model_name, 1536)

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        response = self.client.embeddings.create(
            input=text,
            model=self.model_name
        )
        return np.array(response.data[0].embedding)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Embed a batch of text strings."""
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [np.array(item.embedding) for item in response.data]

    def get_dimension(self) -> int:
        """Return the dimension of embeddings."""
        return self.dimension


class EmbedderFactory:
    """Factory for creating embedder instances."""

    @staticmethod
    def create_embedder(
        provider: str,
        model: str = None,
        **kwargs
    ) -> EmbedderInterface:
        """
        Create an embedder instance.

        Args:
            provider: Provider name ('sentence_transformers' or 'openai')
            model: Model name
            **kwargs: Additional provider-specific arguments

        Returns:
            EmbedderInterface instance
        """
        if provider.lower() == "sentence_transformers":
            model = model or "all-MiniLM-L6-v2"
            return SentenceTransformerEmbedder(model_name=model)
        elif provider.lower() == "openai":
            model = model or "text-embedding-ada-002"
            return OpenAIEmbedder(
                model_name=model,
                api_key=kwargs.get('api_key'),
                endpoint=kwargs.get('endpoint')
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
