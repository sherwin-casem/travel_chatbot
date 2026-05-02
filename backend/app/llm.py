from __future__ import annotations

import json
import logging

from openai import APIConnectionError, APIStatusError, APIError, APITimeoutError, OpenAI, RateLimitError

from app.config import settings
from app.exceptions import LLMError
from app.schemas import LLMStructuredResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a travel agency assistant. Answer ONLY using the KNOWLEDGE CONTEXT below.
If the context does not contain enough information, say clearly what is missing and suggest contacting support.
Do not invent policies, prices, deadlines, or links not implied by the context.

Always respond with a single JSON object (no markdown) matching this shape:
{
  "answer": "clear markdown-safe plain text answer for the customer",
  "booking_link": "URL path or full URL; may be empty string if not applicable",
  "related_services": [ {"name": "short label", "reason": "one sentence why it helps"} ],
  "escalate_to_human": false,
  "escalation_reason": null
}

Rules:
- Keep "answer" concise but actionable (2–6 short paragraphs max unless the user asked for detail).
- Put at most 3 items in related_services; only suggest services relevant to the question.
- Set escalate_to_human true if the user needs exceptions, disputes, bespoke multi-leg trips, or anything not covered in context.
- When escalating, set escalation_reason to a short internal note; still give a helpful partial answer in "answer" if possible.
"""


def _format_context(passages: list[tuple[str, str, int | None]]) -> str:
    blocks = []
    for i, (text, source, page) in enumerate(passages, start=1):
        loc = source
        if page:
            loc = f"{source} (page {page})"
        blocks.append(f"[{i}] {loc}\n{text.strip()}")
    return "\n\n---\n\n".join(blocks)


def generate_reply(
    user_message: str,
    history: list[dict],
    passages: list[tuple[str, str, int | None]],
) -> LLMStructuredResponse:
    if not settings.openai_api_key.strip():
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    client = OpenAI(api_key=settings.openai_api_key)
    ctx = _format_context(passages)
    msgs: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-settings.max_context_messages :]:
        msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append(
        {
            "role": "user",
            "content": (
                f"KNOWLEDGE CONTEXT:\n{ctx}\n\n---\n"
                f"Defaults: primary booking URL base is {settings.booking_base_url}. "
                f"Human support: {settings.support_contact_label} at {settings.support_contact_url}.\n"
                f"Customer message:\n{user_message}"
            ),
        },
    )

    try:
        completion = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=msgs,
            temperature=0.35,
            response_format={"type": "json_object"},
        )
    except RateLimitError as e:
        logger.warning("OpenAI rate limited: %s", e)
        raise LLMError("The assistant is temporarily rate-limited. Try again shortly.", code="LLM_RATE_LIMIT", cause=e) from e
    except APIConnectionError as e:
        logger.warning("OpenAI connection error: %s", e)
        raise LLMError("Could not reach the language model service.", code="LLM_CONNECTION", cause=e) from e
    except APITimeoutError as e:
        logger.warning("OpenAI timeout: %s", e)
        raise LLMError("The language model request timed out.", code="LLM_TIMEOUT", cause=e) from e
    except APIStatusError as e:
        logger.warning("OpenAI API error: %s", e)
        raise LLMError("The language model service returned an error.", code="LLM_UPSTREAM", cause=e) from e
    except APIError as e:
        logger.warning("OpenAI API error (generic): %s", e)
        raise LLMError("The language model service returned an error.", code="LLM_UPSTREAM", cause=e) from e
    except Exception as e:  # pragma: no cover
        logger.exception("Unexpected OpenAI client error")
        raise LLMError("Unexpected error calling the language model.", code="LLM_UNEXPECTED", cause=e) from e

    raw = completion.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("LLM returned non-JSON: %s", raw[:500])
        raise LLMError("Model returned invalid JSON.", code="LLM_BAD_JSON", cause=e) from e

    try:
        return LLMStructuredResponse.model_validate(data)
    except Exception as e:
        logger.warning("LLM JSON failed validation: %s", e)
        raise LLMError("Model response had an unexpected shape.", code="LLM_BAD_SHAPE", cause=e) from e
