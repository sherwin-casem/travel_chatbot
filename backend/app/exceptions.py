from __future__ import annotations

from typing import Optional


class EmbeddingsNotConfiguredError(Exception):
    """No working embedding backend (e.g. missing OPENAI_API_KEY)."""


class RetrievalError(Exception):
    """Vector store or embedding query failed."""

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        self.cause = cause
        super().__init__(message)


class LLMError(Exception):
    """Upstream LLM or response parsing failed."""

    def __init__(self, message: str, code: str = "LLM_ERROR", cause: Optional[Exception] = None) -> None:
        self.code = code
        self.cause = cause
        super().__init__(message)
