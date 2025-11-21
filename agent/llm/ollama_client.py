"""
PHASE 9.1: Ollama Integration

Ollama client for local LLM inference (Llama 3, Mistral, etc.).
Provides privacy, cost reduction, and offline capabilities.

Features:
- Async HTTP client for Ollama API
- Model management (list, pull, delete)
- Chat completions with streaming support
- Token counting and performance metrics
- Graceful error handling and retries
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx


@dataclass
class OllamaModel:
    """Represents an Ollama model."""
    name: str
    size: int
    modified_at: str
    digest: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OllamaModel:
        """Create OllamaModel from API response."""
        return cls(
            name=data.get("name", ""),
            size=data.get("size", 0),
            modified_at=data.get("modified_at", ""),
            digest=data.get("digest", ""),
        )


@dataclass
class OllamaResponse:
    """Represents an Ollama chat response."""
    model: str
    response: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second for response generation."""
        if self.eval_count and self.eval_duration:
            # Duration is in nanoseconds, convert to seconds
            duration_seconds = self.eval_duration / 1e9
            return self.eval_count / duration_seconds if duration_seconds > 0 else 0.0
        return 0.0

    @property
    def latency_seconds(self) -> float:
        """Calculate total latency in seconds."""
        if self.total_duration:
            return self.total_duration / 1e9
        return 0.0


class OllamaClient:
    """
    Ollama local LLM client.

    Provides async interface to Ollama API for local model inference.
    Supports chat completions, streaming, and model management.

    Example:
        >>> client = OllamaClient()
        >>> response = await client.chat("What is Python?", model="llama3")
        >>> print(response.response)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 180.0,
        max_retries: int = 3,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            timeout: Request timeout in seconds (default: 180s for local inference)
            max_retries: Maximum number of retries on failure (default: 3)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)
        self._is_available: Optional[bool] = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def is_available(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is reachable, False otherwise
        """
        if self._is_available is not None:
            return self._is_available

        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            self._is_available = response.status_code == 200
            return self._is_available
        except Exception as e:
            print(f"[Ollama] Server not available: {e}")
            self._is_available = False
            return False

    async def list_models(self) -> List[OllamaModel]:
        """
        Get list of available models.

        Returns:
            List of OllamaModel objects

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self.client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()

        data = response.json()
        models = [OllamaModel.from_dict(m) for m in data.get("models", [])]
        return models

    async def pull_model(self, model: str) -> bool:
        """
        Pull/download a model from Ollama registry.

        Args:
            model: Model name (e.g., "llama3", "mistral")

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"[Ollama] Pulling model: {model}")

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=600.0,  # 10 minutes for model download
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "digest" in data:
                            print(f"[Ollama] {status}: {data.get('digest', '')[:12]}...")
                        else:
                            print(f"[Ollama] {status}")

                        if data.get("status") == "success":
                            print(f"[Ollama] Successfully pulled {model}")
                            return True

            return True

        except Exception as e:
            print(f"[Ollama] Failed to pull model {model}: {e}")
            return False

    async def delete_model(self, model: str) -> bool:
        """
        Delete a model from local storage.

        Args:
            model: Model name

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.delete(
                f"{self.base_url}/api/delete",
                json={"name": model}
            )
            response.raise_for_status()
            print(f"[Ollama] Deleted model: {model}")
            return True
        except Exception as e:
            print(f"[Ollama] Failed to delete model {model}: {e}")
            return False

    async def chat(
        self,
        prompt: str,
        model: str = "llama3",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        context: Optional[List[int]] = None,
    ) -> OllamaResponse:
        """
        Send chat request to Ollama.

        Args:
            prompt: User prompt/question
            model: Model name (default: "llama3")
            system: System prompt/instructions
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            context: Context from previous conversation

        Returns:
            OllamaResponse with generated text and metadata

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        request_data: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            request_data["system"] = system

        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens

        if context:
            request_data["context"] = context

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json=request_data,
                )
                response.raise_for_status()

                data = response.json()

                # Calculate total duration if not provided
                if "total_duration" not in data:
                    data["total_duration"] = int((time.time() - start_time) * 1e9)

                return OllamaResponse(
                    model=data.get("model", model),
                    response=data.get("response", ""),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    prompt_eval_duration=data.get("prompt_eval_duration"),
                    eval_count=data.get("eval_count"),
                    eval_duration=data.get("eval_duration"),
                )

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"[Ollama] Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    print(f"[Ollama] Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[Ollama] All retries failed: {e}")

        # If all retries failed, raise the last error
        raise last_error  # type: ignore

    async def chat_stream(
        self,
        prompt: str,
        model: str = "llama3",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Send chat request with streaming response.

        Args:
            prompt: User prompt/question
            model: Model name (default: "llama3")
            system: System prompt/instructions
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Yields:
            Chunks of generated text as they arrive

        Example:
            >>> async for chunk in client.chat_stream("Tell me a story"):
            >>>     print(chunk, end="", flush=True)
        """
        request_data: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            request_data["system"] = system

        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=request_data,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]

                    if data.get("done", False):
                        break

    async def embeddings(self, text: str, model: str = "llama3") -> List[float]:
        """
        Generate embeddings for text.

        Args:
            text: Text to embed
            model: Model name

        Returns:
            List of embedding values
        """
        response = await self.client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()

        data = response.json()
        return data.get("embedding", [])
