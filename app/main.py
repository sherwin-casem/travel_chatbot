from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.chat_service import ChatService
from app.config import settings
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(
    title="Travel Agency Concierge",
    description="RAG-powered customer assistant with retrieval, structured answers, and escalation.",
    version="0.1.0",
)

_static = Path(__file__).resolve().parent.parent / "static"
if _static.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static)), name="static")

_chat = ChatService()


def _kb_ready() -> tuple[bool, int]:
    import chromadb

    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        coll = client.get_collection(name=settings.collection_name)
        n = coll.count()
        return True, n
    except Exception:
        return False, 0


@app.get("/api/health")
def health() -> dict:
    ready, n = _kb_ready()
    return {
        "status": "ok" if ready and n else "degraded",
        "kb_chunks": n,
        "chroma_path": settings.chroma_path,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    ready, n = _kb_ready()
    if not ready or n == 0:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not indexed. Run: python -m app.ingest",
        )
    try:
        return _chat.chat(body.message, body.session_id)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/")
def index() -> FileResponse:
    index_path = _static / "index.html"
    if not index_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="static/index.html missing — run from project root.",
        )
    return FileResponse(index_path)
