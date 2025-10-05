"""Markdown chunking module using mistune parser."""

from typing import List, Dict, Any
import mistune
from mistune import BlockState


class Chunk:
    """Represents a chunk of text with metadata."""

    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

    def __repr__(self):
        return f"Chunk(text={self.text[:50]}..., metadata={self.metadata})"


class MarkdownChunker:
    """Chunks markdown documents by headers while preserving structure."""

    def __init__(self, max_chunk_size: int = 512, overlap: int = 50):
        """
        Initialize the markdown chunker.

        Args:
            max_chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.markdown = mistune.create_markdown(renderer='ast')

    def chunk_document(self, text: str, source: str = None) -> List[Chunk]:
        """
        Chunk a markdown document by headers.

        Args:
            text: The markdown text to chunk
            source: Optional source identifier (e.g., file path)

        Returns:
            List of Chunk objects with text and metadata
        """
        # Parse markdown to AST
        ast = self.markdown(text)

        # Extract chunks based on headers
        chunks = []
        current_chunk = []
        current_headers = []
        chunk_position = 0

        for token in ast:
            if token['type'] == 'heading':
                # Save previous chunk if it exists
                if current_chunk:
                    chunk_text = self._join_tokens(current_chunk)
                    chunks.extend(self._split_if_needed(
                        chunk_text,
                        current_headers.copy(),
                        chunk_position,
                        source
                    ))
                    chunk_position += 1

                # Update header hierarchy
                level = token['attrs']['level']
                header_text = self._extract_text(token['children'])

                # Trim headers to current level
                current_headers = [
                    h for h in current_headers if h['level'] < level
                ]
                current_headers.append({
                    'level': level,
                    'text': header_text
                })

                # Start new chunk with header
                current_chunk = [token]
            else:
                current_chunk.append(token)

        # Add final chunk
        if current_chunk:
            chunk_text = self._join_tokens(current_chunk)
            chunks.extend(self._split_if_needed(
                chunk_text,
                current_headers.copy(),
                chunk_position,
                source
            ))

        return chunks

    def _extract_text(self, tokens: List[Dict]) -> str:
        """Extract plain text from tokens."""
        text_parts = []
        for token in tokens:
            if isinstance(token, dict):
                if token['type'] == 'text':
                    text_parts.append(token['raw'])
                elif 'children' in token:
                    text_parts.append(self._extract_text(token['children']))
            elif isinstance(token, str):
                text_parts.append(token)
        return ''.join(text_parts)

    def _join_tokens(self, tokens: List[Dict]) -> str:
        """Convert tokens back to markdown text."""
        text_parts = []
        for token in tokens:
            if token['type'] == 'heading':
                level = token['attrs']['level']
                header_text = self._extract_text(token['children'])
                text_parts.append(f"{'#' * level} {header_text}\n\n")
            elif token['type'] == 'paragraph':
                para_text = self._extract_text(token['children'])
                text_parts.append(f"{para_text}\n\n")
            elif token['type'] == 'block_code':
                lang = token.get('attrs', {}).get('info', '')
                code = token['raw']
                text_parts.append(f"```{lang}\n{code}\n```\n\n")
            elif token['type'] == 'list':
                # Simplified list rendering
                list_text = self._extract_text(token['children'])
                text_parts.append(f"{list_text}\n\n")
            else:
                # Generic fallback
                if 'raw' in token:
                    text_parts.append(token['raw'])
                elif 'children' in token:
                    text_parts.append(self._extract_text(token['children']))

        return ''.join(text_parts).strip()

    def _split_if_needed(
        self,
        text: str,
        headers: List[Dict],
        position: int,
        source: str = None
    ) -> List[Chunk]:
        """Split text into smaller chunks if it exceeds max_chunk_size."""
        if len(text) <= self.max_chunk_size:
            return [Chunk(
                text=text,
                metadata={
                    'headers': headers,
                    'position': position,
                    'source': source
                }
            )]

        # Split into smaller chunks with overlap
        chunks = []
        start = 0
        sub_position = 0

        while start < len(text):
            end = start + self.max_chunk_size
            chunk_text = text[start:end]

            chunks.append(Chunk(
                text=chunk_text,
                metadata={
                    'headers': headers,
                    'position': position,
                    'sub_position': sub_position,
                    'source': source
                }
            ))

            start = end - self.overlap
            sub_position += 1

        return chunks
