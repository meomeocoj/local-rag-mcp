"""Markdown chunking module using LangChain MarkdownHeaderTextSplitter."""

from typing import List, Dict, Any
from langchain_text_splitters import MarkdownHeaderTextSplitter


class Chunk:
    """Represents a chunk of text with metadata."""

    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

    def __repr__(self):
        return f"Chunk(text={self.text[:50]}..., metadata={self.metadata})"


class MarkdownChunker:
    """Chunks markdown documents by headers while preserving structure."""

    def __init__(self, max_chunk_size: int = 1024, overlap: int = 100, strategy: str = "headers", max_tokens_per_chunk: int = 5000):
        """
        Initialize the markdown chunker.

        Args:
            max_chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            strategy: Chunking strategy (only "headers" supported with LangChain)
            max_tokens_per_chunk: Maximum tokens per chunk (default: 5000, safely under 5461 limit)
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.strategy = strategy
        self.max_tokens_per_chunk = max_tokens_per_chunk

        # Initialize LangChain MarkdownHeaderTextSplitter
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6"),
        ]

    def chunk_document(self, text: str, source: str = None) -> List[Chunk]:
        """
        Chunk a markdown document by headers.

        Args:
            text: The markdown text to chunk
            source: Optional source identifier (e.g., file path)

        Returns:
            List of Chunk objects with text and metadata
        """
        # Handle empty input
        if not text or not text.strip():
            return []

        # Create LangChain splitter
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False  # Keep headers in chunks for context
        )

        # Split text by headers
        langchain_docs = splitter.split_text(text)

        # If no documents returned or text has no headers, handle as headerless
        if not langchain_docs:
            return self._handle_headerless_document(text, source)

        # Convert LangChain Documents to our Chunk format
        chunks = []
        for position, doc in enumerate(langchain_docs):
            # Extract headers from metadata
            headers = self._extract_headers_from_metadata(doc.metadata)

            # Get chunk text
            chunk_text = doc.page_content

            # Enforce token limit (rough estimate: 1 token ≈ 4 characters)
            estimated_tokens = len(chunk_text) // 4

            # If chunk exceeds token limit or character size, split it recursively
            if estimated_tokens > self.max_tokens_per_chunk or len(chunk_text) > self.max_chunk_size:
                split_chunks = self._split_large_chunk(chunk_text, headers, position, source)
                chunks.extend(split_chunks)
            else:
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata={
                        'headers': headers,
                        'position': position,
                        'source': source or ""
                    }
                ))

        # Renumber positions after splitting
        for idx, chunk in enumerate(chunks):
            chunk.metadata['position'] = idx

        return chunks

    def _extract_headers_from_metadata(self, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract header hierarchy from LangChain metadata."""
        headers = []

        # LangChain stores headers as "Header 1", "Header 2", etc.
        for i in range(1, 7):
            header_key = f"Header {i}"
            if header_key in metadata:
                headers.append({
                    'level': i,
                    'text': metadata[header_key]
                })

        return headers

    def _handle_headerless_document(self, text: str, source: str = None) -> List[Chunk]:
        """Handle documents without headers."""
        # If small enough, return as single chunk
        if len(text) <= self.max_chunk_size:
            return [Chunk(
                text=text,
                metadata={
                    'headers': [],
                    'position': 0,
                    'source': source or ""
                }
            )]

        # Otherwise, split by character limit with overlap
        chunks = []
        start = 0
        position = 0

        while start < len(text):
            end = start + self.max_chunk_size
            chunk_text = text[start:end]

            chunks.append(Chunk(
                text=chunk_text,
                metadata={
                    'headers': [],
                    'position': position,
                    'source': source or "",
                    'recursive_chunk': True
                }
            ))

            start = end - self.overlap if self.overlap > 0 else end
            position += 1

        return chunks

    def _split_large_chunk(
        self,
        text: str,
        headers: List[Dict],
        position: int,
        source: str = None
    ) -> List[Chunk]:
        """Split large chunks that exceed max_chunk_size or token limit with overlap."""
        chunks = []
        start = 0
        sub_position = 0

        # Calculate safe chunk size based on token limit (1 token ≈ 4 chars)
        max_chars_from_tokens = self.max_tokens_per_chunk * 4
        effective_max_size = min(self.max_chunk_size, max_chars_from_tokens)

        while start < len(text):
            end = start + effective_max_size
            chunk_text = text[start:end]

            chunks.append(Chunk(
                text=chunk_text,
                metadata={
                    'headers': headers,
                    'position': position,
                    'sub_position': sub_position,
                    'source': source or "",
                    'recursive_chunk': True
                }
            ))

            start = end - self.overlap if self.overlap > 0 else end
            sub_position += 1

        return chunks
