from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.schemas import ChatResponse


def append_turn(session_id: str, user_message: str, response: ChatResponse) -> None:
    path = Path(settings.log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "user_message": user_message,
        "answer": response.answer,
        "escalated": response.escalated,
        "escalation_reason": response.escalation_reason,
        "sources": [p.model_dump() for p in response.sources],
        "retrieval_confidence": response.retrieval_confidence,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
