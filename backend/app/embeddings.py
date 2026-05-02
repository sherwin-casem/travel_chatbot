import os

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.config import settings
from app.exceptions import EmbeddingsNotConfiguredError


def make_embedding_function():
    """
    Shared embedding function for ingest and query (must match).

    Default: OpenAI embeddings only (reliable on Windows; avoids broken onnxruntime DLLs).

    Set ALLOW_LOCAL_ONNX_EMBEDDINGS=true only on machines where Chroma's ONNX MiniLM loads.
    """
    key = settings.openai_api_key.strip()
    if key:
        os.environ.setdefault("OPENAI_API_KEY", key)
        model = settings.openai_embedding_model or "text-embedding-3-small"
        return OpenAIEmbeddingFunction(api_key=key, model_name=model)

    if not settings.allow_local_onnx_embeddings:
        raise EmbeddingsNotConfiguredError(
            "OPENAI_API_KEY is not set in the repo-root .env file. "
            "Embeddings are required for retrieval and ingest. "
            "Alternatively set ALLOW_LOCAL_ONNX_EMBEDDINGS=true if onnxruntime works on this host."
        )

    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    try:
        return ONNXMiniLM_L6_V2()
    except Exception as e:  # pragma: no cover - platform-specific
        raise EmbeddingsNotConfiguredError(
            "Local ONNX embeddings failed to load (often a missing VC++ runtime or DLL issue). "
            "Set OPENAI_API_KEY in .env, or repair onnxruntime on this machine."
        ) from e
