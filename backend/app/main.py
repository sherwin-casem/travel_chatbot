from __future__ import annotations

import logging
from typing import Any

import chromadb
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.chat_service import ChatService
from app.config import settings
from app.exceptions import EmbeddingsNotConfiguredError, LLMError, RetrievalError
from app.http_errors import AppHTTPException
from app.schemas import ApiErrorResponse, ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Travel Agency Concierge API",
    description="RAG-powered customer assistant (JSON API for the React client).",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_chat = ChatService()


def _error_payload(code: str, message: str, details: Any = None) -> dict:
    body = ApiErrorResponse(error={"code": code, "message": message, "details": details})
    return body.model_dump()


def _kb_ready() -> tuple[bool, int]:
    try:
        client = chromadb.PersistentClient(path=str(settings.chroma_path))
        names = {c.name for c in client.list_collections()}
        if settings.collection_name not in names:
            logger.info(
                "Knowledge base collection %r not found under %s (run ingest).",
                settings.collection_name,
                settings.chroma_path,
            )
            return False, 0
        coll = client.get_collection(name=settings.collection_name)
        n = coll.count()
        return True, n
    except Exception:
        logger.warning("Knowledge base readiness check failed.", exc_info=True)
        return False, 0


def _kb_not_ready_hint() -> str:
    key_set = bool(settings.openai_api_key.strip())
    if not key_set:
        return (
            "OPENAI_API_KEY is missing in the repo-root .env file. "
            "This project uses OpenAI embeddings on hosts where local ONNX fails. "
            "After setting the key, run: cd backend && python -m app.ingest"
        )
    return (
        "The vector index is empty or not initialized. "
        "Run: cd backend && python -m app.ingest"
    )


@app.exception_handler(AppHTTPException)
async def app_http_exception_handler(_request: Request, exc: AppHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, exc.details),
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            "HTTP_ERROR",
            str(exc.detail) if exc.detail else "Request failed",
            None,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_payload("VALIDATION_ERROR", "Invalid request body.", exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_payload("INTERNAL_ERROR", "An unexpected error occurred."),
    )


@app.get("/api/health")
def health() -> dict:
    ready, n = _kb_ready()
    degraded = not ready or n == 0
    return {
        "status": "ok" if not degraded else "degraded",
        "kb_chunks": n,
        "chroma_path": str(settings.chroma_path),
        "hint": _kb_not_ready_hint() if degraded else None,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    ready, n = _kb_ready()
    if not ready or n == 0:
        raise AppHTTPException(
            503,
            "KB_NOT_READY",
            _kb_not_ready_hint(),
        )
    try:
        return _chat.chat(body.message, body.session_id)
    except RetrievalError as e:
        code = (
            "EMBEDDINGS_NOT_CONFIGURED"
            if isinstance(e.cause, EmbeddingsNotConfiguredError)
            else "RETRIEVAL_FAILED"
        )
        raise AppHTTPException(
            503,
            code,
            str(e),
            details={"cause_type": type(e.cause).__name__ if e.cause else None},
        ) from e
    except LLMError as e:
        raise AppHTTPException(502, e.code, str(e)) from e
