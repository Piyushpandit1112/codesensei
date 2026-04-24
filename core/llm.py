"""Unified LLM client with a simple `.chat()` API over Gemini + Groq.

Designed so we can swap providers later (including LangGraph nodes) without
touching callers. Direct SDK usage keeps dependency surface small.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .config import settings

# --- Gemini ----------------------------------------------------------------
_gemini_ready = False


def _ensure_gemini() -> Any:
    global _gemini_ready
    import google.generativeai as genai  # type: ignore

    if not _gemini_ready:
        if not settings.has_gemini:
            raise RuntimeError("GEMINI_API_KEY missing")
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_ready = True
    return genai


# --- Groq ------------------------------------------------------------------
_groq_client: Any = None


def _ensure_groq() -> Any:
    global _groq_client
    from groq import Groq  # type: ignore

    if _groq_client is None:
        if not settings.has_groq:
            raise RuntimeError("GROQ_API_KEY missing")
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


# --- Public API ------------------------------------------------------------
def chat(
    prompt: str,
    *,
    provider: str = "gemini",
    system: str | None = None,
    json_mode: bool = False,
    temperature: float = 0.4,
) -> str:
    """Send a single-shot prompt, get a text reply."""
    if provider == "gemini":
        return _gemini_chat(prompt, system=system, json_mode=json_mode, temperature=temperature)
    if provider == "groq":
        return _groq_chat(prompt, system=system, json_mode=json_mode, temperature=temperature)
    raise ValueError(f"Unknown provider {provider!r}")


def chat_json(prompt: str, *, provider: str = "groq", system: str | None = None,
              temperature: float = 0.3) -> dict:
    """Ask the LLM for JSON and robustly parse it. Auto-falls-back on quota errors."""
    raw = _chat_with_fallback(
        prompt, provider=provider, system=system, json_mode=True, temperature=temperature
    )
    return _parse_json(raw)


def _is_quota_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(s in msg for s in ("429", "quota", "rate limit", "exceeded", "resource_exhausted"))


def _chat_with_fallback(
    prompt: str, *, provider: str, system: str | None, json_mode: bool, temperature: float
) -> str:
    """Try primary provider; on 429/quota errors, fall back to the other provider."""
    order = [provider]
    other = "gemini" if provider == "groq" else "groq"
    order.append(other)
    last_exc: Exception | None = None
    for p in order:
        # Skip providers without keys
        if p == "gemini" and not settings.has_gemini:
            continue
        if p == "groq" and not settings.has_groq:
            continue
        try:
            return chat(prompt, provider=p, system=system, json_mode=json_mode, temperature=temperature)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if not _is_quota_error(e):
                raise
            # else: continue to fallback
    raise last_exc if last_exc else RuntimeError("No LLM provider available")


# --- Providers -------------------------------------------------------------
def _gemini_chat(prompt: str, *, system: str | None, json_mode: bool, temperature: float) -> str:
    genai = _ensure_gemini()
    gen_cfg: dict[str, Any] = {"temperature": temperature}
    if json_mode:
        gen_cfg["response_mime_type"] = "application/json"
    model = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=system or None,
        generation_config=gen_cfg,
    )
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()


def _groq_chat(prompt: str, *, system: str | None, json_mode: bool, temperature: float) -> str:
    client = _ensure_groq()
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs: dict[str, Any] = {"temperature": temperature}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        **kwargs,
    )
    return (resp.choices[0].message.content or "").strip()


# --- JSON parsing ----------------------------------------------------------
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.+?)\s*```", re.DOTALL)


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Strip accidental code fences
    m = _JSON_FENCE.search(text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Best-effort: take substring between first { and last }
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def available_provider() -> str | None:
    # Prefer Groq (higher free-tier limits + faster) over Gemini.
    if settings.has_groq:
        return "groq"
    if settings.has_gemini:
        return "gemini"
    return None
