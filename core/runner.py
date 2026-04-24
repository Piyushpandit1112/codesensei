"""Safe-ish user code runner. Executes Python in a subprocess with a timeout
so we can grade the user's solution against the problem's examples."""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
# Parsing example inputs/outputs
# --------------------------------------------------------------------------- #
def parse_io(text: str) -> Any:
    """Best-effort parser for example strings like:
        'nums = [2,7,11,15], target = 9'   -> {"nums":[...], "target":9}
        '[0, 1]'                            -> [0, 1]
        's = "leetcode"'                    -> {"s":"leetcode"}
    Returns a dict (named kwargs) or a python literal.
    """
    text = (text or "").strip()
    if not text:
        return None

    # Try literal eval first (handles '[0,1]', '5', '"abc"').
    try:
        return ast.literal_eval(text)
    except Exception:
        pass

    # Try kwarg-style: split on top-level commas not inside brackets/quotes.
    kwargs: dict[str, Any] = {}
    buf, depth, in_str, quote = "", 0, False, ""
    parts: list[str] = []
    for ch in text + ",":
        if in_str:
            buf += ch
            if ch == quote:
                in_str = False
            continue
        if ch in ("'", '"'):
            in_str, quote = True, ch
            buf += ch
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            if buf.strip():
                parts.append(buf.strip())
            buf = ""
        else:
            buf += ch

    for p in parts:
        if "=" not in p:
            continue
        k, _, v = p.partition("=")
        k = k.strip()
        v = v.strip()
        try:
            kwargs[k] = ast.literal_eval(v)
        except Exception:
            kwargs[k] = v
    return kwargs or None


# --------------------------------------------------------------------------- #
# Detecting the user's entrypoint function
# --------------------------------------------------------------------------- #
def detect_entrypoint(code: str) -> str | None:
    """Find the 'solution' function. Prefer common LeetCode names, otherwise
    return the first top-level `def` name."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    # Preferred names
    for pref in (
        "solution",
        "twoSum",
        "solve",
        "run",
        "main",
    ):
        if pref in names:
            return pref
    return names[0] if names else None


# --------------------------------------------------------------------------- #
# Running user code
# --------------------------------------------------------------------------- #
@dataclass
class CaseResult:
    idx: int
    inp: str
    expected: str
    got: str
    ok: bool
    stdout: str
    stderr: str
    duration_ms: int


RUNNER_TEMPLATE = r'''
# --- user code ---
{user_code}
# --- harness ---
import json, sys, time, io, contextlib
_fn_name = {fn_name!r}
_cases = {cases!r}

_fn = globals().get(_fn_name)
if _fn is None:
    print(json.dumps({{"__err__": f"function {{_fn_name}} not found"}}))
    sys.exit(0)

_out = []
for c in _cases:
    buf = io.StringIO()
    t0 = time.perf_counter()
    try:
        with contextlib.redirect_stdout(buf):
            args = c["args"]
            if isinstance(args, dict):
                res = _fn(**args)
            elif isinstance(args, (list, tuple)):
                res = _fn(*args)
            else:
                res = _fn(args)
        err = ""
    except Exception as e:
        res = None
        err = f"{{type(e).__name__}}: {{e}}"
    dt = int((time.perf_counter() - t0) * 1000)
    _out.append({{
        "got": repr(res),
        "stdout": buf.getvalue()[-2000:],
        "stderr": err,
        "ms": dt,
    }})

print("<<RESULT>>" + json.dumps(_out))
'''


def run_cases(code: str, cases: list[dict], timeout: float = 5.0) -> tuple[str, list[CaseResult]]:
    """Execute `code` in a subprocess against `cases` and return (fn_name, results).

    Each case dict: {"args": dict|list|literal, "expected": any, "input_label": str}.
    """
    fn_name = detect_entrypoint(code) or "solution"

    # serialise cases as plain python repr-friendly structures
    safe_cases = [
        {"args": c["args"], "expected": c.get("expected"), "label": c.get("input_label", "")}
        for c in cases
    ]

    script = RUNNER_TEMPLATE.format(
        user_code=code,
        fn_name=fn_name,
        cases=safe_cases,
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(script)
        path = fh.name

    results: list[CaseResult] = []
    try:
        proc = subprocess.run(
            [sys.executable, "-I", path],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        payload = None
        if "<<RESULT>>" in stdout:
            try:
                payload = json.loads(stdout.split("<<RESULT>>", 1)[1].strip())
            except Exception:
                payload = None

        if not payload:
            # Global failure — return a single error row
            err_text = (stderr or stdout or "no output").strip()[-800:]
            return fn_name, [
                CaseResult(
                    idx=i,
                    inp=str(c.get("input_label", "")),
                    expected=repr(c.get("expected")),
                    got="(no result)",
                    ok=False,
                    stdout="",
                    stderr=err_text,
                    duration_ms=0,
                )
                for i, c in enumerate(safe_cases)
            ]

        for i, (c, r) in enumerate(zip(safe_cases, payload)):
            got_repr = r.get("got", "")
            exp = c.get("expected")
            exp_repr = repr(exp)
            ok = False
            try:
                got_val = ast.literal_eval(got_repr)
                ok = _loose_eq(got_val, exp)
            except Exception:
                ok = got_repr.strip() == exp_repr.strip()
            results.append(
                CaseResult(
                    idx=i,
                    inp=str(c.get("label", "")),
                    expected=exp_repr,
                    got=got_repr,
                    ok=ok,
                    stdout=r.get("stdout", ""),
                    stderr=r.get("stderr", ""),
                    duration_ms=int(r.get("ms", 0)),
                )
            )
        return fn_name, results

    except subprocess.TimeoutExpired:
        return fn_name, [
            CaseResult(
                idx=i, inp=str(c.get("input_label", "")),
                expected=repr(c.get("expected")),
                got="(timeout)", ok=False,
                stdout="", stderr=f"timeout after {timeout}s",
                duration_ms=int(timeout * 1000),
            )
            for i, c in enumerate(safe_cases)
        ]
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass


def _loose_eq(a: Any, b: Any) -> bool:
    """Compare with tolerance for 'return value is a list of indices where order
    does not matter but length does' — common in LeetCode easies."""
    if a == b:
        return True
    try:
        if isinstance(a, list) and isinstance(b, list):
            if len(a) == len(b) and sorted(a) == sorted(b):
                return True
    except Exception:
        pass
    return False


# --------------------------------------------------------------------------- #
# Build runnable cases from the ProblemMeta.examples list
# --------------------------------------------------------------------------- #
def cases_from_examples(examples) -> list[dict]:
    """Convert ProblemMeta.examples -> [{'args':..., 'expected':..., 'input_label':...}]."""
    out = []
    for ex in examples or []:
        args = parse_io(ex.input)
        expected = parse_io(ex.output)
        out.append({
            "args": args if args is not None else {},
            "expected": expected,
            "input_label": ex.input,
        })
    return out


# --------------------------------------------------------------------------- #
# Java / C++ compiler availability — used by UI to show "run" vs "reference"
# --------------------------------------------------------------------------- #
def has_java() -> bool:
    return bool(shutil.which("javac") and shutil.which("java"))


def has_cpp() -> bool:
    return bool(shutil.which("g++") or shutil.which("clang++"))


def language_status() -> dict[str, dict]:
    """Report which languages can be executed on this machine."""
    return {
        "python": {"available": True,          "msg": "Python always runs (via subprocess)."},
        "java":   {"available": has_java(),    "msg": "Requires `javac` + `java` on PATH. Reference editor only if missing."},
        "cpp":    {"available": has_cpp(),     "msg": "Requires `g++` or `clang++` on PATH. Reference editor only if missing."},
    }
