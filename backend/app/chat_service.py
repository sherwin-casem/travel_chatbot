from __future__ import annotations

import uuid

from app.config import settings
from app.conversation_log import append_turn
from app.escalation import should_escalate_precheck, should_escalate_retrieval
from app.llm import generate_reply
from app.retrieval import retrieve
from app.schemas import ChatResponse, RetrievedPassage


class ChatService:
    """In-memory sessions (MVP)."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}

    def chat(self, message: str, session_id: str | None) -> ChatResponse:
        sid = session_id or str(uuid.uuid4())
        if sid not in self._sessions:
            self._sessions[sid] = []

        pre_esc, pre_reason = should_escalate_precheck(message)
        passages, confidence = retrieve(message)
        sources: list[RetrievedPassage] = passages

        low_ctx, low_reason = should_escalate_retrieval(
            confidence,
            threshold=settings.similarity_threshold,
        )

        passage_tuples = [(p.text, p.source, p.page) for p in passages[: settings.retrieval_top_k]]

        try:
            parsed = generate_reply(message, self._sessions[sid], passage_tuples)
        except RuntimeError as e:
            answer = (
                f"I am not fully configured yet: {e}. "
                f"You can still reach us at {settings.support_contact_url}."
            )
            out = ChatResponse(
                session_id=sid,
                answer=answer,
                booking_link=None,
                related_services=[],
                escalated=True,
                escalation_reason="LLM not configured",
                support_url=settings.support_contact_url,
                sources=sources,
                retrieval_confidence=confidence,
            )
            self._sessions[sid].append({"role": "user", "content": message})
            self._sessions[sid].append({"role": "assistant", "content": out.answer})
            append_turn(sid, message, out)
            return out

        escalate = pre_esc or low_ctx or parsed.escalate_to_human
        reason = (
            pre_reason
            or low_reason
            or parsed.escalation_reason
            or ("Model suggested human review." if parsed.escalate_to_human else None)
        )

        booking_link = (parsed.booking_link or "").strip() or settings.booking_base_url
        related = parsed.related_services[:3]

        if escalate and reason:
            note = f"\n\n---\n**{settings.support_contact_label}:** [{settings.support_contact_url}]({settings.support_contact_url})\n*{reason}*"
            answer = parsed.answer.strip() + note
        else:
            answer = parsed.answer.strip()

        out = ChatResponse(
            session_id=sid,
            answer=answer,
            booking_link=booking_link,
            related_services=related,
            escalated=bool(escalate),
            escalation_reason=reason if escalate else None,
            support_url=settings.support_contact_url if escalate else None,
            sources=sources,
            retrieval_confidence=confidence,
        )

        self._sessions[sid].append({"role": "user", "content": message})
        self._sessions[sid].append({"role": "assistant", "content": out.answer})
        append_turn(sid, message, out)
        return out
