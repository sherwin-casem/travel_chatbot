import os

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.config import settings


def make_embedding_function():
    """
    Shared embedding function for ingest and query (must match).

    Prefer OpenAI embeddings when OPENAI_API_KEY is set (no local ONNX/torch DLLs).
    Otherwise use Chroma's ONNX MiniLM (requires working onnxruntime).
    """
    key = settings.openai_api_key.strip()
    if key:
        os.environ.setdefault("OPENAI_API_KEY", key)
        model = settings.openai_embedding_model or "text-embedding-3-small"
        return OpenAIEmbeddingFunction(api_key=key, model_name=model)

    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    try:
        return ONNXMiniLM_L6_V2()
    except Exception as e:  # pragma: no cover - platform-specific
        raise RuntimeError(
            "Local ONNX embeddings failed to load. Set OPENAI_API_KEY in .env to use "
            "OpenAI embeddings instead, or install the Visual C++ Redistributable and "
            "verify onnxruntime works on this machine."
        ) from e
