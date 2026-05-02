from __future__ import annotations

import logging

import chromadb

from app.config import settings
from app.embeddings import make_embedding_function
from app.exceptions import EmbeddingsNotConfiguredError, RetrievalError
from app.schemas import RetrievedPassage

logger = logging.getLogger(__name__)


def get_collection():
    try:
        ef = make_embedding_function()
        client = chromadb.PersistentClient(path=str(settings.chroma_path))
        return client.get_collection(
            name=settings.collection_name,
            embedding_function=ef,
        )
    except EmbeddingsNotConfiguredError as e:
        logger.warning("Embeddings unavailable: %s", e)
        raise RetrievalError(str(e), cause=e) from e
    except Exception as e:
        logger.exception("Failed to open Chroma collection")
        raise RetrievalError("Could not open the vector index.", cause=e) from e


def retrieve(query: str, top_k: int | None = None) -> tuple[list[RetrievedPassage], float]:
    """
    Return passages and a coarse confidence score in [0, 1] from best cosine-related distance.
    """
    k = top_k or settings.retrieval_top_k
    try:
        coll = get_collection()
        raw = coll.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
    except RetrievalError:
        raise
    except Exception as e:
        logger.exception("Vector query failed")
        raise RetrievalError("Semantic search failed.", cause=e) from e

    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    dists = (raw.get("distances") or [[]])[0]

    passages: list[RetrievedPassage] = []
    sims: list[float] = []
    for text, meta, dist in zip(docs, metas, dists, strict=False):
        if not text:
            continue
        page = meta.get("page")
        try:
            p_int: int | None = int(page) if page is not None and int(page) > 0 else None
        except (TypeError, ValueError):
            p_int = None
        sim = 1.0 - float(dist) if dist is not None else 0.0
        sims.append(max(0.0, min(1.0, sim)))
        passages.append(
            RetrievedPassage(
                text=text,
                source=str(meta.get("source", "")),
                page=p_int,
                distance=float(dist) if dist is not None else None,
            ),
        )

    confidence = max(sims) if sims else 0.0
    return passages, confidence
