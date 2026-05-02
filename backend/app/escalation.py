from __future__ import annotations

import re

_AMBIGUOUS_PATTERNS = [
    r"\b(or worse|i don't know how|complicated|complex)\b",
    r"\b(multiple cities|multi[- ]?stop|round[\s-]?the[\s-]?world)\b",
    r"\b(visa|immigration|legal|lawyer|insurance claim|complaint|refund\s+not|chargeback)\b",
]

_DIRECT_ESCALATION = [
    "human",
    "agent",
    "representative",
    "speak to someone",
    "talk to a person",
    "customer service",
    "real person",
    "manager",
    "supervisor",
]


def should_escalate_precheck(message: str) -> tuple[bool, str | None]:
    """Fast routing before retrieval/LLM."""
    lowered = message.lower().strip()
    if len(lowered) < 2:
        return True, "Empty or unclear request."

    for phrase in _DIRECT_ESCALATION:
        if phrase in lowered:
            return True, "You asked to reach a human representative."

    if len(lowered) > 400:
        return True, "This request is long and detailed; a specialist can handle it more reliably."

    for pat in _AMBIGUOUS_PATTERNS:
        if re.search(pat, lowered, re.IGNORECASE):
            return True, "This topic often needs a human specialist (policy or itinerary specifics)."

    return False, None


def should_escalate_retrieval(confidence: float, threshold: float) -> tuple[bool, str | None]:
    if confidence < threshold:
        return (
            True,
            "I could not find closely matching information in our current knowledge base.",
        )
    return False, None
