import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    source: str
    page: int | None
    section_hint: str | None


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    *,
    source: str,
    page: int | None,
    chunk_size: int = 900,
    overlap: int = 120,
) -> list[TextChunk]:
    """Split long text into overlapping windows with metadata."""
    text = normalize_text(text)
    if not text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end]
        if end < n:
            break_at = piece.rfind(". ")
            if break_at > chunk_size // 2:
                piece = piece[: break_at + 1]
                end = start + len(piece)
        section_hint = _infer_section(piece)
        chunks.append(
            TextChunk(
                text=piece.strip(),
                source=source,
                page=page,
                section_hint=section_hint,
            ),
        )
        if end >= n:
            break
        start = max(0, end - overlap)

    return chunks


def _infer_section(piece: str) -> str | None:
    first = piece.split("\n", 1)[0].strip()
    if len(first) < 80 and first.isupper():
        return first.title()
    m = re.match(r"^(\d+(?:\.\d+)*)\s+(.{3,80})$", first)
    if m:
        return m.group(2).strip()
    return None
