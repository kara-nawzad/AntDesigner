"""Server-side AETHER/Groq adapter.

Conversation history remains in the browser and is sent with each request.  This
module retains the configured model fallback order while keeping the
GROQ_API_KEY entirely on the server.
"""
from __future__ import annotations

import os
from typing import Any

# Model preference order for server-side Groq requests.
AETHER_MODELS = (
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
)

NOT_CONFIGURED_MESSAGE = (
    "Set GROQ_API_KEY in `.env` or the server environment or your environment to enable "
    "AETHER Assistant."
)


def configured() -> bool:
    """Whether a server-side Groq key is available, without exposing it."""
    return bool(os.getenv("GROQ_API_KEY", "").strip())


def complete(messages: list[dict[str, str]], preferred_model: str | None = None) -> dict[str, Any]:
    """Request a chat completion using the legacy fallback order.

    No user content is logged.  The returned model identifier lets the browser send
    it back as ``preferred_model`` on its next request, matching the browser's "last working model first" behavior without retaining conversations on
    the server.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return {
            "status": "not_configured",
            "reply": NOT_CONFIGURED_MESSAGE,
            "model": None,
        }

    try:
        from groq import AuthenticationError as GroqAuthError
        from groq import Groq
    except Exception:
        return {
            "status": "unavailable",
            "reply": "AETHER is temporarily unavailable. Try again later.",
            "model": None,
        }

    ordered = []
    if preferred_model in AETHER_MODELS:
        ordered.append(preferred_model)
    ordered.extend(model for model in AETHER_MODELS if model != preferred_model)

    try:
        client = Groq(api_key=api_key)
    except Exception:
        return {
            "status": "unavailable",
            "reply": "AETHER is temporarily unavailable. Try again later.",
            "model": None,
        }

    for model_id in ordered:
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=messages,
            )
            reply = completion.choices[0].message.content
            if reply:
                return {"status": "ok", "reply": str(reply), "model": model_id}
        except GroqAuthError:
            return {
                "status": "invalid_key",
                "reply": (
                    "Invalid Groq API key. In Fly.io secrets set `GROQ_API_KEY` "
                    "to a valid key from console.groq.com/keys."
                ),
                "model": None,
            }
        except Exception:
            # A deprecated/busy model is expected to fail sometimes; try the next
            # legacy fallback without surfacing provider internals to the browser.
            continue

    return {
        "status": "unavailable",
        "reply": (
            "AETHER is temporarily unavailable (all Groq models were rejected). "
            "Try again later or check your API key."
        ),
        "model": None,
    }
