"""Classify, hint, solve, and generate animation frames via the LLM."""
from __future__ import annotations

from . import cache, llm, prompts
from .schemas import FrameScript, ProblemMeta, Solution


# --- Classification --------------------------------------------------------
def classify(problem: str) -> ProblemMeta:
    def _run() -> dict:
        provider = llm.available_provider() or "groq"
        return llm.chat_json(
            prompts.render("classify", problem=problem),
            provider=provider,
        )

    data = cache.memoise("classify", problem, producer=_run)
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
    def _run() -> dict:
        provider = llm.available_provider() or "groq"
        return llm.chat_json(
            prompts.render("solver", problem=problem),
            provider=provider,
            temperature=0.3,
        )

    data = cache.memoise("solve_v3", problem, producer=_run)
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
