"""Generate large batches of test cases for a problem via LLM.

Key design: the LLM is notoriously bad at computing expected outputs
(e.g. claiming "IIV" -> 6 for Roman numerals). So we let the LLM propose
only the INPUTS, and we compute the TRUE expected output by running a
trusted reference solution (the tutor's verified Python code) in a sandbox.
Any input that makes the reference crash is discarded.
"""
from __future__ import annotations

import json
from typing import Any

from . import cache
from .runner import parse_io, run_cases


SYSTEM_INPUTS = (
    "You are an expert DSA test-case generator. Produce STRICT JSON only: a "
    "list of diverse test INPUTS for the given problem. Cover edge cases "
    "(small/empty/single/duplicates/negatives/zeros/boundary/extremes/already-"
    "sorted/reverse-sorted/etc.). DO NOT compute the expected output — we will "
    "run a reference solution to get the truth.\n\n"
    "Each element of the returned list must be of the form:\n"
    "  {\"input\": \"<kwarg-style input line>\", "
    "\"label\": \"<short human label>\"}\n"
    "The input string MUST follow the SAME format as the examples below "
    "(same kwarg names, matching quoting for strings). "
    "Every generated input MUST satisfy the problem's constraints exactly "
    "(e.g. for Roman numerals, only produce VALID Roman numerals built from "
    "I,V,X,L,C,D,M; for sorted-array problems, the array MUST be sorted; etc.).\n"
    "Return JSON only — no markdown fences."
)

USER_TEMPLATE = (
    "PROBLEM:\n{problem}\n\n"
    "EXAMPLE INPUTS (follow this exact format):\n{examples}\n\n"
    "Return {n} diverse, VALID test inputs."
)


def _call_llm(problem: str, examples_block: str, n: int) -> list[dict]:
    """Ask the LLM for a JSON array of inputs."""
    prompt = USER_TEMPLATE.format(problem=problem, examples=examples_block, n=n)

    try:
        from groq import Groq  # type: ignore
        from .config import settings
        if settings.groq_api_key:
            client = Groq(api_key=settings.groq_api_key)
            resp = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SYSTEM_INPUTS},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.6,
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        return v
                return []
            return data if isinstance(data, list) else []
    except Exception:
        pass

    try:
        import google.generativeai as genai  # type: ignore
        from .config import settings
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            out = model.generate_content(
                SYSTEM_INPUTS + "\n\n" + prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            raw = (out.text or "{}").strip()
            data = json.loads(raw)
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        return v
                return []
            return data if isinstance(data, list) else []
    except Exception:
        pass

    return []


def generate(
    problem: str,
    examples: list,
    reference_code: str,
    n: int = 30,
    visible: int = 3,
) -> list[dict]:
    """Generate VALIDATED test cases.

    1. Ask LLM for `n` diverse INPUTS (no outputs).
    2. Run `reference_code` (trusted Python) against each input.
    3. Keep only inputs where the reference returned cleanly.
    4. Use the reference's return value as the ground-truth `expected`.

    Result is cached keyed on problem + reference_code.
    """
    ex_lines = []
    for ex in (examples or [])[:3]:
        ex_lines.append(f"  input : {ex.input}\n  output: {ex.output}")
    ex_block = "\n\n".join(ex_lines) if ex_lines else "(no examples)"

    def _run() -> list[dict]:
        # Seed: always include the examples as visible, verified cases.
        seed_cases: list[dict] = []
        for ex in examples or []:
            args = parse_io(ex.input)
            expected = parse_io(ex.output)
            seed_cases.append({
                "input_label": ex.input,
                "args": args if args is not None else {},
                "expected": expected,
                "label": "from problem examples",
                "hidden": False,
            })

        # Propose inputs via LLM.
        raw = _call_llm(problem, ex_block, n)
        proposed: list[dict] = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            inp = str(item.get("input", "")).strip()
            if not inp:
                continue
            args = parse_io(inp)
            proposed.append({
                "input_label": inp,
                "args": args if args is not None else {},
                "expected": None,       # filled below
                "label": str(item.get("label") or f"case {i + 1}"),
                "hidden": True,
            })

        # Validate by running the reference solution.
        if reference_code and proposed:
            try:
                _, ref_results = run_cases(
                    reference_code,
                    [{"args": p["args"], "expected": None,
                      "input_label": p["input_label"]} for p in proposed],
                    timeout=15.0,
                )
            except Exception:
                ref_results = []

            validated: list[dict] = []
            import ast
            for p, r in zip(proposed, ref_results):
                if r.stderr or r.got in ("(timeout)", "(no result)"):
                    continue
                try:
                    got_val = ast.literal_eval(r.got)
                except Exception:
                    continue
                p["expected"] = got_val
                validated.append(p)
            proposed = validated

        merged = seed_cases + proposed
        # Ensure visibility matches policy.
        for idx, case in enumerate(merged):
            case["hidden"] = idx >= visible
        return merged

    # Cache by problem text + reference code (so a corrected reference regenerates).
    cache_key = f"tests_v2::{n}::{visible}::{hash(reference_code)}"
    return cache.memoise(cache_key, problem, producer=_run) or []
