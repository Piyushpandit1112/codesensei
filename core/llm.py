"""Unified LLM client with a simple `.chat()` API over multiple providers.

Providers (in fallback order): Groq → Cerebras → OpenRouter → Gemini.
All four have a free tier; if one is rate-limited we try the next.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .config import settings


class NeedsClarification(RuntimeError):
    """Raised when no LLM provider could answer (all quotas exhausted, or
    the model returned unparseable output). The UI should ask the user to
    rephrase / give an example, instead of showing a stack trace."""

    def __init__(self, message: str, *, problem: str = "", reason: str = ""):
        super().__init__(message)
        self.problem = problem
        self.reason = reason

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
    if provider == "cerebras":
        return _cerebras_chat(prompt, system=system, json_mode=json_mode, temperature=temperature)
    if provider == "openrouter":
        return _openrouter_chat(prompt, system=system, json_mode=json_mode, temperature=temperature)
    raise ValueError(f"Unknown provider {provider!r}")


def chat_json(prompt: str, *, provider: str = "groq", system: str | None = None,
              temperature: float = 0.3) -> dict:
    """Ask the LLM for JSON and robustly parse it. Auto-falls-back on quota errors."""
    raw = _chat_with_fallback(
        prompt, provider=provider, system=system, json_mode=True, temperature=temperature
    )
    return _parse_json(raw)


def _is_quota_error(exc: BaseException) -> bool:
    """Return True if this error should trigger trying the next provider.

    Covers: rate-limits / quota exhaustion AND transient network failures
    (DNS, connect, timeout) — because all of those are recoverable by
    falling through to a different host.
    """
    msg = str(exc).lower()
    if any(s in msg for s in (
        "429", "quota", "rate limit", "exceeded", "resource_exhausted",
        "too many requests", "overloaded", "billing",
        # Network / DNS / connect issues — retry on next provider.
        "getaddrinfo", "name or service not known", "nodename nor servname",
        "temporary failure in name resolution", "dns",
        "connection", "connecterror", "connectionerror",
        "timeout", "timed out", "read timeout", "connect timeout",
        "ssl", "handshake", "remote disconnected", "broken pipe",
        "network is unreachable", "no route to host",
    )):
        return True
    # httpx / urllib3 / requests typed exceptions.
    name = type(exc).__name__.lower()
    return any(s in name for s in (
        "connecterror", "connecttimeout", "readtimeout", "timeout",
        "dnserror", "networkerror", "transporterror", "remoteprotocolerror",
    ))


# Order: try the providers most likely to succeed (high free quota + speed) first.
_FALLBACK_ORDER = ("groq", "cerebras", "openrouter", "gemini")


def _provider_available(p: str) -> bool:
    if p == "groq":       return settings.has_groq
    if p == "gemini":     return settings.has_gemini
    if p == "cerebras":   return settings.has_cerebras
    if p == "openrouter": return settings.has_openrouter
    return False


def _chat_with_fallback(
    prompt: str, *, provider: str, system: str | None, json_mode: bool, temperature: float
) -> str:
    """Try preferred provider; on 429/quota errors, fall back through the chain."""
    # Build the order: preferred first, then all the others.
    order = [provider] + [p for p in _FALLBACK_ORDER if p != provider]
    last_exc: Exception | None = None
    tried: list[str] = []
    for p in order:
        if not _provider_available(p):
            continue
        tried.append(p)
        try:
            return chat(prompt, provider=p, system=system, json_mode=json_mode, temperature=temperature)
        except ModuleNotFoundError as e:
            # Provider SDK isn't installed — silently skip to next provider.
            last_exc = e
            continue
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if not _is_quota_error(e):
                raise
            # quota / rate limit / network — try the next provider
    if last_exc:
        raise RuntimeError(
            f"All LLM providers exhausted (tried: {', '.join(tried) or 'none'}). "
            f"Last error: {last_exc}"
        ) from last_exc
    raise RuntimeError(
        "No LLM provider configured. Set at least one of "
        "GROQ_API_KEY / CEREBRAS_API_KEY / OPENROUTER_API_KEY / GEMINI_API_KEY."
    )


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
    """Call Groq. If the primary model is over its per-day token budget,
    automatically retry on a smaller model with a separate, larger quota.

    Free-tier Groq has per-model daily token limits. The 70B model fills
    quickly (100k TPD) while llama-3.1-8b-instant has 500k TPD — plenty
    of headroom for one more session.
    """
    client = _ensure_groq()
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs: dict[str, Any] = {"temperature": temperature}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    # Try the configured primary model, then a fallback small model.
    models_to_try = [settings.groq_model]
    fallback = "llama-3.1-8b-instant"
    if fallback not in models_to_try:
        models_to_try.append(fallback)

    last_exc: Exception | None = None
    for m in models_to_try:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=messages,
                **kwargs,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            last_exc = e
            msg = str(e).lower()
            # Only retry on per-model quota / rate-limit errors. Other
            # errors (auth, malformed request) should fail fast.
            if not any(s in msg for s in (
                "rate_limit", "rate limit", "tokens per day",
                "tokens_per_day", "tpd", "tpm", "429", "quota",
            )):
                raise
            # else: try the next model
    if last_exc:
        raise last_exc
    raise RuntimeError("Groq: no models configured")


# --- OpenAI-compatible REST helpers (Cerebras, OpenRouter) -----------------
def _openai_compat_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    system: str | None,
    json_mode: bool,
    temperature: float,
    extra_headers: dict[str, str] | None = None,
) -> str:
    if not api_key:
        raise RuntimeError("API key missing")
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    resp = httpx.post(
        f"{base_url}/chat/completions",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    if resp.status_code == 429:
        raise RuntimeError(f"429 quota: {resp.text[:300]}")
    resp.raise_for_status()
    data = resp.json()
    try:
        return (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected response shape: {data}") from e


def _cerebras_chat(prompt: str, *, system: str | None, json_mode: bool, temperature: float) -> str:
    return _openai_compat_chat(
        base_url="https://api.cerebras.ai/v1",
        api_key=settings.cerebras_api_key,
        model=settings.cerebras_model,
        prompt=prompt, system=system, json_mode=json_mode, temperature=temperature,
    )


def _openrouter_chat(prompt: str, *, system: str | None, json_mode: bool, temperature: float) -> str:
    return _openai_compat_chat(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        prompt=prompt, system=system, json_mode=json_mode, temperature=temperature,
        extra_headers={
            "HTTP-Referer": "https://codesensei.streamlit.app",
            "X-Title": "CodeSensei",
        },
    )


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
    """Pick the best default provider that has a key configured."""
    for p in _FALLBACK_ORDER:
        if _provider_available(p):
            return p
    return None
