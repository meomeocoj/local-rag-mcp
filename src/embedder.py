"""Embedding interface and implementations."""

from abc import ABC, abstractmethod
from typing import List
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
        endpoint: str = None,
        batch_size: int = 32
    ):
        """
        Initialize the OpenAI embedder.

        Args:
            model_name: Name of the OpenAI embedding model
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            endpoint: Optional custom endpoint
            batch_size: Maximum batch size for embeddings (default: 32)
        """
        from openai import OpenAI

        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=endpoint)
        self.batch_size = batch_size

        # Dimension mapping for known models
        self.dimension_map = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        self.dimension = self.dimension_map.get(model_name, 1536)

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        text = text if text else "No information"

        response = self.client.embeddings.create(
            input=text,
            model=self.model_name
        )
        return np.array(response.data[0].embedding)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Embed a batch of text strings with token-aware batching."""
        processed_texts = [
            text if text else "No information"
            for text in texts
        ]

        # CRITICAL: Filter out oversized individual texts that exceed single-item API limit
        # API has max 5461 tokens per REQUEST (not per item)
        # So if a SINGLE item exceeds ~5000 tokens, it will fail even when sent alone
        MAX_TOKENS_PER_ITEM = 5000  # Conservative single-item limit
        filtered_texts = []
        skipped_count = 0

        for i, text in enumerate(processed_texts):
            estimated_tokens = len(text) // 4
            if estimated_tokens > MAX_TOKENS_PER_ITEM:
                print(f"[WARNING] Skipping oversized chunk {i+1}: {len(text)} chars, ~{estimated_tokens} tokens")
                skipped_count += 1
            else:
                filtered_texts.append(text)

        if skipped_count > 0:
            print(f"[WARNING] Skipped {skipped_count} oversized chunks")

        processed_texts = filtered_texts

        # OpenAI embedding API limits:
        # - Max ~5461 token limit per REQUEST (entire batch combined)
        # - Also seems to have a hard limit on number of inputs per request
        # Use VERY conservative limits since our estimation is inaccurate
        MAX_TOKENS_PER_BATCH = 1000  # Much more conservative due to estimation errors
        MAX_ITEMS_PER_BATCH = 5  # Reduced from 10

        embeddings = []
        current_batch = []
        current_tokens = 0

        for text in processed_texts:
            # Estimate tokens (rough approximation: chars / 4)
            estimated_tokens = len(text) // 4

            # If adding this text would exceed limit, process current batch first
            if current_batch and (
                current_tokens + estimated_tokens > MAX_TOKENS_PER_BATCH or
                len(current_batch) >= MAX_ITEMS_PER_BATCH
            ):
                try:
                    response = self.client.embeddings.create(
                        input=current_batch,
                        model=self.model_name
                    )
                    embeddings.extend([np.array(item.embedding) for item in response.data])
                except Exception as e:
                    # If batch fails, process items individually
                    print(f"[WARNING] Batch of {len(current_batch)} failed, retrying individually: {e}")
                    for single_text in current_batch:
                        try:
                            response = self.client.embeddings.create(
                                input=[single_text],
                                model=self.model_name
                            )
                            embeddings.extend([np.array(item.embedding) for item in response.data])
                        except Exception as e2:
                            print(f"[WARNING] Skipping chunk - failed to embed: {e2}")
                            # Add None placeholder to maintain index alignment
                            embeddings.append(None)

                # Reset batch
                current_batch = []
                current_tokens = 0

            # Add text to current batch
            current_batch.append(text)
            current_tokens += estimated_tokens

        # Process remaining batch
        if current_batch:
            try:
                response = self.client.embeddings.create(
                    input=current_batch,
                    model=self.model_name
                )
                embeddings.extend([np.array(item.embedding) for item in response.data])
            except Exception as e:
                print(f"[WARNING] Final batch of {len(current_batch)} failed, retrying individually: {e}")
                for single_text in current_batch:
                    try:
                        response = self.client.embeddings.create(
                            input=[single_text],
                            model=self.model_name
                        )
                        embeddings.extend([np.array(item.embedding) for item in response.data])
                    except Exception as e2:
                        print(f"[WARNING] Skipping chunk - failed to embed: {e2}")
                        embeddings.append(None)

        # Filter out None values and return only successful embeddings
        valid_embeddings = [e for e in embeddings if e is not None]
        failed_count = len(embeddings) - len(valid_embeddings)

        if failed_count > 0:
            print(f"[WARNING] Failed to embed {failed_count}/{len(embeddings)} chunks")

        return valid_embeddings

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
                endpoint=kwargs.get('endpoint'),
                batch_size=kwargs.get('batch_size', 32)
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
