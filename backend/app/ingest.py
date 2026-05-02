"""
Load PDFs and plain-text FAQs from the repo `data/` tree into ChromaDB.

Run from repo root:
  cd backend && ..\\.venv\\Scripts\\python -m app.ingest
(or activate venv first, cwd=backend)
"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader

from app.chunking import chunk_text
from app.config import settings
from app.embeddings import make_embedding_function
from app.exceptions import EmbeddingsNotConfiguredError

try:
    import chromadb
except ImportError as e:  # pragma: no cover
    raise SystemExit("Install dependencies: pip install -r requirements.txt") from e


def _read_pdf(path: Path) -> list[tuple[str | None, int]]:
    reader = PdfReader(str(path))
    pages: list[tuple[str | None, int]] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            t = page.extract_text()
        except Exception:
            t = None
        pages.append((t, i))
    return pages


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def collect_documents(root: Path) -> list[tuple[str, str, int | None]]:
    """Return list of (text, source_id, page_or_none)."""
    out: list[tuple[str, str, int | None]] = []

    for path in sorted(root.rglob("*.pdf")):
        rel = path.relative_to(root).as_posix()
        for text, page in _read_pdf(path):
            if text and text.strip():
                out.append((text, f"{rel}#p{page}", page))

    for ext in (".md", ".txt", ".faq"):
        for path in sorted(root.rglob(f"*{ext}")):
            if path.suffix.lower() != ext:
                continue
            rel = path.relative_to(root).as_posix()
            body = _read_text_file(path)
            out.append((body, rel, None))

    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            rel = path.relative_to(root).as_posix()
            buf: list[str] = []
            for item in data:
                if isinstance(item, dict):
                    q = item.get("question") or item.get("q")
                    a = item.get("answer") or item.get("a")
                    if q and a:
                        buf.append(f"Q: {q}\nA: {a}")
                elif isinstance(item, str):
                    buf.append(item)
            if buf:
                out.append(("\n\n".join(buf), rel, None))

    return out


def main() -> None:
    root = settings.data_dir
    if not root.is_dir():
        raise SystemExit(f"Data directory not found: {root.resolve()}")

    ef = make_embedding_function()
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    coll = client.get_or_create_collection(
        name=settings.collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    existing = coll.get(include=[])
    if existing and existing.get("ids"):
        coll.delete(ids=existing["ids"])

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    doc_index = 0
    for text, source_id, page in collect_documents(root):
        for ch in chunk_text(text, source=source_id, page=page):
            ids.append(f"doc-{doc_index}")
            doc_index += 1
            documents.append(ch.text)
            metadatas.append(
                {
                    "source": ch.source,
                    "page": ch.page if ch.page is not None else -1,
                    "section_hint": ch.section_hint or "",
                },
            )

    if not documents:
        raise SystemExit("No text extracted from data/. Add PDFs or .md/.txt FAQs.")

    batch = 128
    for i in range(0, len(documents), batch):
        coll.add(
            ids=ids[i : i + batch],
            documents=documents[i : i + batch],
            metadatas=metadatas[i : i + batch],
        )

    print(f"Ingested {len(documents)} chunks into {settings.chroma_path}")


if __name__ == "__main__":
    try:
        main()
    except EmbeddingsNotConfiguredError as e:
        raise SystemExit(f"Cannot ingest: {e}") from e
