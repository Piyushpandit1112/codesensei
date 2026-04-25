"""Classify, hint, solve, and generate animation frames via the LLM."""
from __future__ import annotations

import json

from . import cache, llm, prompts
from .schemas import FrameScript, ProblemMeta, Solution

# Re-export so callers can `from core.tutor import NeedsClarification`.
NeedsClarification = llm.NeedsClarification


def _safe_chat_json(prompt: str, *, problem: str, temperature: float = 0.3) -> dict:
    """Run llm.chat_json; convert provider/parse failures into NeedsClarification."""
    provider = llm.available_provider() or "groq"
    try:
        return llm.chat_json(prompt, provider=provider, temperature=temperature)
    except llm.NeedsClarification:
        raise
    except json.JSONDecodeError as e:
        raise NeedsClarification(
            "I couldn't read the model's answer. Could you tell me more about this "
            "problem — for example, give one sample input and the expected output?",
            problem=problem,
            reason=f"json: {e}",
        ) from e
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        network_markers = (
            "provider", "quota", "429", "rate", "exhausted", "api key", "missing",
            "getaddrinfo", "dns", "connection", "timeout", "timed out",
            "ssl", "network", "unreachable", "no route", "name resolution",
        )
        if any(s in msg for s in network_markers):
            raise NeedsClarification(
                "I couldn't reach any AI provider right now (network or quota issue). "
                "Check your internet, then click try-again. Or tell me more about the "
                "problem (a sample input/output works great) and I'll retry.",
                problem=problem,
                reason=str(e),
            ) from e
        raise


# --- Classification --------------------------------------------------------
def classify(problem: str) -> ProblemMeta:
    def _run() -> dict:
        return _safe_chat_json(
            prompts.render("classify", problem=problem),
            problem=problem,
        )

    try:
        data = cache.memoise("classify_v2", problem, producer=_run)
    except NeedsClarification:
        # Don't block intake — just return an empty meta so UI can proceed.
        return ProblemMeta()
    try:
        return ProblemMeta(**data)
    except Exception:
        return ProblemMeta()


# --- Hints -----------------------------------------------------------------
def hint(problem: str, level: int, approach: str = "") -> str:
    level = max(1, min(4, level))

    def _run() -> str:
        provider = llm.available_provider() or "groq"
        if not provider:
            return _offline_hint(level)
        return llm.chat(
            prompts.render("hints", problem=problem, level=level, approach=approach),
            provider=provider,
            temperature=0.5,
        )

    return cache.memoise("hint", problem, level, approach, producer=_run)


def _offline_hint(level: int) -> str:
    return [
        "Hint 1: What information do you look up repeatedly? Can a dictionary help?",
        "Hint 2: For each element, what *complement* are you searching for?",
        "Hint 3: Walk the array once, store seen values in a hash map keyed by value.",
        "Hint 4: `for i, x in enumerate(nums): if target-x in seen: return [seen[target-x], i]; seen[x]=i`",
    ][level - 1]


# --- Solve -----------------------------------------------------------------
def solve(problem: str) -> Solution:
    """Generate a Solution. We validate Pydantic BEFORE caching, so a
    malformed LLM response is never written to disk — retrying actually
    re-calls the LLM instead of returning the same bad data forever."""

    def _run() -> dict:
        data = _safe_chat_json(
            prompts.render("solver", problem=problem),
            problem=problem,
            temperature=0.3,
        )
        # Validate eagerly. If invalid, raise so cache.memoise does NOT
        # store this dict — next call will retry the LLM cleanly.
        Solution(**data)
        return data

    try:
        data = cache.memoise("solve_v4", problem, producer=_run)
    except NeedsClarification:
        raise
    except Exception as e:
        raise NeedsClarification(
            "I got an answer but couldn't fit it into a solution shape. "
            "Could you share a small example (input → expected output) so I "
            "understand what you want?",
            problem=problem,
            reason=str(e),
        ) from e
    return Solution(**data)


# --- Animation frames ------------------------------------------------------
def frames(problem: str, solution: Solution, lang: str = "hinglish") -> FrameScript:
    def _run() -> dict:
        provider = llm.available_provider() or "groq"
        return llm.chat_json(
            prompts.render(
                "animation",
                problem=problem,
                approach=solution.approach_name + " — " + solution.intuition,
                code=solution.code.python or "",
                lang=lang,
            ),
            provider=provider,
            temperature=0.3,
        )

    data = cache.memoise("frames_v2", problem, lang, producer=_run)
    try:
        return FrameScript(**data)
    except Exception:
        return FrameScript()
