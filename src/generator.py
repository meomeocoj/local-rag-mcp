"""Generation module using LiteLLM for unified LLM interface."""

from typing import List, Dict, Any, Optional, Iterator
import litellm


class Generator:
    """Generates answers using LLM with retrieved context."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 512
    ):
        """
        Initialize the generator.

        Args:
            provider: LLM provider (openai, anthropic, cohere, etc.)
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(
        self,
        query: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate an answer based on query and context.

        Args:
            query: User query
            context: Retrieved context chunks
            system_prompt: Optional system prompt

        Returns:
            Generated answer
        """
        # Format context
        context_text = self._format_context(context)

        # Build messages
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant. Answer the question based on the provided context."
            })

        # Add user message with context and query
        user_message = f"""Context:
{context_text}

Question: {query}

Please provide a clear and concise answer based on the context above."""

        messages.append({
            "role": "user",
            "content": user_message
        })

        # Generate response
        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content

    def generate_stream(
        self,
        query: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        """
        Generate an answer with streaming.

        Args:
            query: User query
            context: Retrieved context chunks
            system_prompt: Optional system prompt

        Yields:
            Chunks of the generated answer
        """
        # Format context
        context_text = self._format_context(context)

        # Build messages
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant. Answer the question based on the provided context."
            })

        user_message = f"""Context:
{context_text}

Question: {query}

Please provide a clear and concise answer based on the context above."""

        messages.append({
            "role": "user",
            "content": user_message
        })

        # Generate streaming response
        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context chunks into a readable string."""
        formatted_chunks = []

        for i, item in enumerate(context, 1):
            chunk_text = item.get('document', '')
            metadata = item.get('metadata', {})

            # Add source information if available
            source = metadata.get('source', 'Unknown')
            headers = metadata.get('headers', [])

            header_path = ' > '.join([h.get('text', '') for h in headers]) if headers else ''

            if header_path:
                formatted_chunks.append(
                    f"[{i}] From {source} - {header_path}:\n{chunk_text}"
                )
            else:
                formatted_chunks.append(
                    f"[{i}] From {source}:\n{chunk_text}"
                )

        return '\n\n'.join(formatted_chunks)
