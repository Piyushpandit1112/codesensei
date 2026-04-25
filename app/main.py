"""CodeSensei — Streamlit entrypoint (v0 prototype, Solve page only)."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so `core` is importable when Streamlit
# runs this file directly (script dir, not CWD, is added by default).
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Streamlit Cloud secrets bridge
# ---------------------------------------------------------------------------
# On Streamlit Community Cloud the API keys are configured via the "Secrets"
# UI and surfaced through `st.secrets`. Locally we use a `.env` file. Mirror
# any st.secrets entries into os.environ BEFORE importing `core.config` so
# pydantic-settings picks them up regardless of where the app is running.
try:
    if hasattr(st, "secrets"):
        for _k, _v in dict(st.secrets).items():
            if isinstance(_v, (str, int, float, bool)) and _k not in os.environ:
                os.environ[_k] = str(_v)
except Exception:
    pass

from core import animator, demo, tutor
from core.config import settings
from core.schemas import FrameScript, ProblemMeta, Solution

try:
    from streamlit_ace import st_ace
    _HAS_ACE = True
except Exception:
    _HAS_ACE = False

from core import runner as code_runner
from core import tests_gen

st.set_page_config(page_title="CodeSensei — Hindi DSA Tutor", page_icon="🧠", layout="wide")

# ---------------------------------------------------------------------------
# Custom CSS — modern dark theme
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root { --accent:#6c8cff; --accent2:#b06bff; --ok:#34d399; --warn:#fbbf24; }
    .stApp { background:
        radial-gradient(1200px 500px at 0% -10%, rgba(108,140,255,.10), transparent 60%),
        radial-gradient(900px 400px at 100% 110%, rgba(176,107,255,.08), transparent 60%),
        linear-gradient(180deg, #0b1020, #10172f) !important;
    }
    .block-container { padding-top: 1.6rem; max-width: 1400px; }
    h1, h2, h3 { letter-spacing: -0.01em; }
    h1 { background: linear-gradient(90deg, #93a9ff, #d4aaff);
         -webkit-background-clip: text; background-clip: text;
         -webkit-text-fill-color: transparent; font-weight: 800; }
    .stButton > button {
        border-radius: 10px; border: 1px solid #2a3356;
        background: rgba(255,255,255,.04); color: #e7ecff;
        padding: 0.55rem 1rem; font-weight: 600;
        transition: transform .15s ease, background .2s ease;
    }
    .stButton > button:hover { transform: translateY(-1px); background: rgba(255,255,255,.08); }
    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #6c8cff, #4f6ff0) !important;
        border-color: #6c8cff !important; color: white !important;
        box-shadow: 0 10px 24px rgba(108,140,255,.35);
    }
    /* Cards */
    .cs-card {
        background: #1a2140; border: 1px solid #2a3356; border-radius: 14px;
        padding: 16px 18px; box-shadow: 0 20px 40px rgba(0,0,0,.25);
    }
    .cs-chip {
        display:inline-block; padding:6px 12px; margin:4px 6px 4px 0;
        border-radius:999px; font-size:13px; font-weight:700;
        background: linear-gradient(90deg, rgba(108,140,255,.18), rgba(176,107,255,.18));
        border: 1px solid #3a4476; color: #e7ecff;
    }
    .cs-diff-easy   { background: rgba(52,211,153,.18); color:#6ee7b7; border:1px solid rgba(52,211,153,.4);
                      padding:2px 10px; border-radius:999px; font-size:12px; font-weight:700; }
    .cs-diff-medium { background: rgba(251,191,36,.18); color:#fcd34d; border:1px solid rgba(251,191,36,.4);
                      padding:2px 10px; border-radius:999px; font-size:12px; font-weight:700; }
    .cs-diff-hard   { background: rgba(248,113,113,.18); color:#fca5a5; border:1px solid rgba(248,113,113,.4);
                      padding:2px 10px; border-radius:999px; font-size:12px; font-weight:700; }
    .cs-sim {
        background:#131a35; border:1px solid #2a3356; border-radius:12px;
        padding:12px 14px; margin-bottom:10px;
    }
    .cs-sim a { color:#93a9ff; text-decoration:none; font-weight:700; }
    .cs-sim a:hover { text-decoration:underline; }
    .cs-tip {
        background: linear-gradient(90deg, rgba(108,140,255,.08), rgba(176,107,255,.04));
        border-left: 3px solid #6c8cff; border-radius: 8px;
        padding: 10px 14px; margin: 6px 0; font-size: 14px;
    }
    .cs-follow {
        background: rgba(251,191,36,.08); border-left: 3px solid #fbbf24;
        border-radius: 8px; padding: 10px 14px; margin: 6px 0; font-size: 14px;
    }
    /* ---- Detailed tab cards ---- */
    .cs-step {
        display:flex; gap:12px; align-items:flex-start;
        background:#131a35; border:1px solid #2a3356; border-radius:10px;
        padding:12px 14px; margin:8px 0;
    }
    .cs-step-num {
        flex:0 0 32px; height:32px; border-radius:50%;
        display:flex; align-items:center; justify-content:center;
        font-weight:800; color:#fff; font-size:13px;
        background: linear-gradient(180deg,#6c8cff,#4f6ff0);
        box-shadow: 0 4px 10px rgba(108,140,255,.35);
    }
    .cs-step-body { flex:1; font-size:14px; line-height:1.6; color:#e7ecff; }
    .cs-dry {
        font-family: ui-monospace, "Cascadia Code", monospace;
        background:#0f1530; border:1px solid #2a3356; border-radius:8px;
        padding:10px 14px; font-size:13px; color:#c9d2f5; margin:4px 0;
        border-left:3px solid #6c8cff; white-space:pre-wrap;
    }
    .cs-big-o {
        display:inline-block; font-family:ui-monospace,monospace;
        font-size:22px; font-weight:800; padding:6px 14px; border-radius:10px;
        background: linear-gradient(90deg, rgba(108,140,255,.25), rgba(176,107,255,.18));
        border:1px solid #6c8cff; color:#fff;
    }
    .cs-pit {
        background: rgba(248,113,113,.08); border-left:3px solid #f87171;
        border-radius:8px; padding:12px 14px; margin:8px 0;
        display:flex; gap:10px; align-items:flex-start;
    }
    .cs-pit-ico { font-size:20px; flex:0 0 auto; }
    .cs-pit-body { color:#fecaca; font-size:14px; line-height:1.55; }
    .cs-alt {
        background:#131a35; border:1px solid #2a3356; border-radius:10px;
        padding:14px 16px; margin:8px 0;
    }
    .cs-alt-head { display:flex; gap:10px; align-items:center; margin-bottom:6px; flex-wrap:wrap; }
    .cs-alt-name { font-size:15px; font-weight:800; color:#e7ecff; }
    .cs-alt-bigo {
        font-family:ui-monospace,monospace; font-size:12px; font-weight:700;
        padding:3px 10px; border-radius:999px;
        background:rgba(251,191,36,.15); color:#fcd34d; border:1px solid rgba(251,191,36,.4);
    }
    .cs-alt-trade { color:#c9d2f5; font-size:13.5px; line-height:1.55; }
    [data-testid="stMetricValue"] { font-weight: 800; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("stage", "intake")          # intake | think | hints | solved
ss.setdefault("problem", "")
ss.setdefault("approach", "")
ss.setdefault("think_started_at", None)
ss.setdefault("meta", None)
ss.setdefault("hints_shown", 0)
ss.setdefault("hint_texts", [])
ss.setdefault("solution", None)
ss.setdefault("frames", None)
ss.setdefault("audio_map", {})
ss.setdefault("stitched_uri", "")
ss.setdefault("frame_ends", [])
ss.setdefault("is_demo", False)
ss.setdefault("user_code", "")
ss.setdefault("user_code_java", "")
ss.setdefault("user_code_cpp", "")
ss.setdefault("active_lang", "python")
ss.setdefault("run_results", None)
ss.setdefault("run_fn", "")
ss.setdefault("test_cases", None)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🧠 CodeSensei")
    st.caption("Hindi / Hinglish DSA tutor — think first, then learn visually.")

    _voice_list = ["amol", "arvind", "meera", "diya"]
    _voice_labels = {
        "amol":  "Amol — deep baritone male (Amitabh-style)",
        "arvind": "Arvind — warm male teacher",
        "meera": "Meera — warm female",
        "diya":  "Diya — young female",
    }
    _default_voice = settings.default_voice if settings.default_voice in _voice_list else "amol"
    voice = st.selectbox(
        "Voice (Sarvam Bulbul)",
        _voice_list,
        index=_voice_list.index(_default_voice),
        format_func=lambda v: _voice_labels.get(v, v),
        help="Natural Indian voices. Amol = deep male (Amitabh-ish). Arvind = warm teacher.",
    )
    lang = st.radio(
        "Language style",
        ["hinglish", "hindi"],
        index=0 if settings.default_lang == "hinglish" else 1,
        horizontal=True,
    )
    think_secs = st.slider("Think-first timer (seconds)", 30, 600, settings.think_seconds, 30)

    st.divider()
    st.subheader("Status")
    st.write(f"Groq: {'✅' if settings.has_groq else '❌'}")
    st.write(f"Cerebras: {'✅' if settings.has_cerebras else '❌'}")
    st.write(f"OpenRouter: {'✅' if settings.has_openrouter else '❌'}")
    st.write(f"Gemini: {'✅' if settings.has_gemini else '❌'}")
    st.write(f"Sarvam TTS: {'✅' if settings.has_sarvam else '⚠️ browser fallback'}")

    st.divider()
    if st.button("📖 Load Two Sum demo (offline)", use_container_width=True):
        ss.problem = demo.PROBLEM
        ss.meta = demo.META
        ss.solution = demo.SOLUTION
        ss.frames = demo.FRAMES
        ss.is_demo = True
        ss.stage = "think"
        ss.think_started_at = time.time()
        ss.hints_shown = 0
        ss.hint_texts = []
        ss.audio_map = {}
        ss.stitched_uri = ""
        ss.frame_ends = []
        ss.user_code = ""
        ss.user_code_java = ""
        ss.user_code_cpp = ""
        ss.run_results = None
        ss.test_cases = None
        st.rerun()

    if st.button("🔄 Reset session", use_container_width=True):
        for k in list(ss.keys()):
            del ss[k]
        st.rerun()

    if st.button("🧹 Clear LLM cache", use_container_width=True,
                 help="Wipe cached classifications & solutions. Use this if "
                      "the AI ever gives a wrong/garbled answer that keeps "
                      "coming back even after retrying."):
        try:
            from core import cache as _cache_mod
            _cache_mod._cache.clear()
            st.toast("🧹 Cache cleared. Next solve will hit the LLM fresh.", icon="✅")
        except Exception as e:
            st.error(f"Couldn't clear cache: {e}")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("CodeSensei 🧠")
st.caption(
    "**Think-first** · animated walkthrough · natural Indian Hindi narration · "
    "company tags & interview follow-ups."
)

# ---------------------------------------------------------------------------
# Stage: INTAKE
# ---------------------------------------------------------------------------
if ss.stage == "intake":
    st.subheader("1️⃣ Paste the problem")
    txt = st.text_area(
        "Problem statement",
        height=200,
        placeholder="e.g. Given an array of integers nums and a target, return indices of the two numbers that add up to target… Or just type a famous title like 'two sum', '4 sum', '0/1 knapsack'.",
    )
    col_a, _ = st.columns([1, 3])
    if col_a.button("🚀 Start session", type="primary", disabled=not txt.strip()):
        # If the user typed a short famous title, auto-expand it to the
        # canonical statement (with examples + constraints) before any
        # LLM call. This fixes "0 test cases" + "couldn't reach AI" for
        # very short inputs that the LLM can't classify.
        from core import known_problems
        expanded, matched = known_problems.expand_if_known(txt.strip())
        ss.problem = expanded
        if matched is not None:
            st.toast(f"📚 Recognised famous problem: {matched.title}", icon="✨")
        ss.is_demo = False
        with st.spinner("Classifying…"):
            try:
                ss.meta = tutor.classify(ss.problem)
            except Exception:
                ss.meta = ProblemMeta()
        ss.stage = "think"
        ss.think_started_at = time.time()
        ss.hints_shown = 0
        ss.hint_texts = []
        st.rerun()
    st.info(
        "💡 **Shortcut:** type just **'two sum'**, **'4 sum'**, **'0/1 knapsack'**, etc. — "
        "we'll auto-load the full LeetCode statement with examples. Or paste your "
        "own problem with examples for any custom question."
    )

# ---------------------------------------------------------------------------
# Stage: THINK
# ---------------------------------------------------------------------------
elif ss.stage == "think":
    meta: ProblemMeta = ss.meta or ProblemMeta()
    elapsed = int(time.time() - (ss.think_started_at or time.time()))
    remaining = max(0, think_secs - elapsed)

    # ---- Seed test suite with just the examples on entry. ----
    # Hidden LLM-proposed cases are generated (and VALIDATED against a reference
    # solution) only when the user clicks Run, so we never show tests with
    # fabricated expected values.
    if ss.test_cases is None:
        if ss.is_demo:
            ss.test_cases = list(demo.TESTS)
        else:
            seed = code_runner.cases_from_examples(meta.examples or [])
            for c in seed:
                c["label"] = "from problem examples"
                c["hidden"] = False
            ss.test_cases = seed

    tc_all = ss.test_cases or []
    tc_visible = [c for c in tc_all if not c.get("hidden")]
    tc_hidden_n = len(tc_all) - len(tc_visible)

    # ---- Metrics strip -------------------------------------------------
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Topic", meta.topic or "—")
    m2.metric("Difficulty", meta.difficulty or "—")
    m3.metric("⏳ Timer", f"{remaining}s")
    m4.metric("Visible tests", len(tc_visible))
    m5.metric("Hidden tests", tc_hidden_n)

    st.markdown("### 2️⃣ Think & Practice")
    st.caption(
        "Switch between the **📝 Problem**, the **💻 Editor** (Python / Java / C++), "
        "and the **🧪 Tests** tab. Running your code executes it against visible + "
        "hidden cases like LeetCode."
    )

    t_problem, t_editor, t_tests, t_notes = st.tabs([
        "📝 Problem",
        "💻 Editor",
        f"🧪 Tests ({len(tc_all)})",
        "🗒️ Notes & approach",
    ])

    # =================== TAB 1 — PROBLEM ===============================
    with t_problem:
        diff_cls = {
            "Easy": "cs-diff-easy", "Medium": "cs-diff-medium", "Hard": "cs-diff-hard",
        }.get(meta.difficulty or "", "cs-chip")
        st.markdown(
            f'<div class="cs-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'margin-bottom:10px;">'
            f'<div style="font-size:22px;font-weight:800;color:#e7ecff;">'
            f'📝 {meta.title or "Problem"}</div>'
            f'<span class="{diff_cls}">{meta.difficulty or "—"}</span>'
            f'</div>'
            f'<div style="color:#c9d2f5;font-size:15px;line-height:1.7;white-space:pre-wrap;">'
            f'{meta.description or ss.problem}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ---- Plain-English explanation ---------------------------------
        if getattr(meta, "plain_explanation", ""):
            st.markdown(
                f'<div class="cs-card" style="margin-top:12px;'
                f'background:linear-gradient(135deg,#1a2547,#172040);'
                f'border-left:4px solid #7c9cff;padding:14px 16px;">'
                f'<div style="font-size:12px;font-weight:800;color:#a8b8ff;'
                f'letter-spacing:.4px;margin-bottom:6px;">'
                f'💡 WHAT THIS PROBLEM IS ASKING</div>'
                f'<div style="color:#dde4ff;line-height:1.65;font-size:14px;">'
                f'{meta.plain_explanation}</div></div>',
                unsafe_allow_html=True,
            )

        # ---- Variable glossary ----------------------------------------
        variables = getattr(meta, "variables", {}) or {}
        if variables:
            st.markdown("#### 🔤 What each variable means")
            rows = "".join(
                f'<tr><td style="padding:6px 12px;font-family:ui-monospace,monospace;'
                f'color:#7c9cff;font-weight:700;border-bottom:1px solid #2a3158;">'
                f'{name}</td>'
                f'<td style="padding:6px 12px;color:#dde4ff;font-size:13px;'
                f'border-bottom:1px solid #2a3158;">{desc}</td></tr>'
                for name, desc in variables.items()
            )
            st.markdown(
                f'<div class="cs-card" style="padding:6px 0;">'
                f'<table style="width:100%;border-collapse:collapse;">{rows}</table>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if meta.examples:
            st.markdown("#### 📌 Examples — explained step by step")
            for i, ex in enumerate(meta.examples, 1):
                walkthrough_html = ""
                if getattr(ex, "walkthrough", ""):
                    walkthrough_html = (
                        f'<div style="margin-top:10px;padding:10px 12px;'
                        f'background:rgba(124,156,255,.08);border-left:3px solid #5dd2a5;'
                        f'border-radius:6px;color:#dde4ff;font-size:13px;line-height:1.6;">'
                        f'<b style="color:#ffd479;">🧭 How it works:</b> {ex.walkthrough}'
                        f'</div>'
                    )
                st.markdown(
                    f'<div class="cs-sim">'
                    f'<div style="color:#9aa6cf;font-size:11px;font-weight:800;'
                    f'letter-spacing:.08em;text-transform:uppercase;">Example {i}</div>'
                    f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                    f'color:#e7ecff;margin-top:6px;"><b style="color:#7c9cff;">'
                    f'Input:</b> {ex.input}</div>'
                    f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                    f'color:#6ee7b7;"><b>Output:</b> {ex.output}</div>'
                    + (f'<div style="color:#c9d2f5;font-size:13px;margin-top:6px;">'
                       f'<i>💡 {ex.explanation}</i></div>' if ex.explanation else "")
                    + walkthrough_html
                    + '</div>',
                    unsafe_allow_html=True,
                )

        if meta.constraints:
            st.markdown("#### 🔒 Constraints")
            for cc in meta.constraints:
                st.markdown(f"- `{cc}`")

    # =================== TAB 2 — EDITOR ================================
    with t_editor:
        lang_status = code_runner.language_status()
        lang_tabs = st.tabs(["🐍 Python", "☕ Java", "⚡ C++"])

        # ----- Python ---------------------------------------------------
        with lang_tabs[0]:
            if not ss.user_code:
                fn_stub = "solution"
                if meta.title and "two sum" in meta.title.lower():
                    fn_stub = "twoSum"
                ss.user_code = (
                    f"def {fn_stub}(**kwargs):\n"
                    f"    # kwargs is parsed from the example input line.\n"
                    f"    # e.g. for 'nums = [2,7,11,15], target = 9'\n"
                    f"    # do:  nums = kwargs['nums']; target = kwargs['target']\n"
                    f"    # Return the expected output.\n"
                    f"    pass\n"
                )
            if _HAS_ACE:
                val = st_ace(
                    value=ss.user_code,
                    language="python",
                    theme="dracula",
                    keybinding="vscode",
                    font_size=15,
                    tab_size=4,
                    show_gutter=True,
                    show_print_margin=False,
                    wrap=False,
                    auto_update=True,
                    min_lines=28,
                    max_lines=46,
                    key="ace_py",
                )
                ss.user_code = val or ss.user_code
            else:
                ss.user_code = st.text_area(
                    "Python code", value=ss.user_code, height=560,
                    key="code_py_ta", label_visibility="collapsed",
                )

            rc1, rc2, rc3 = st.columns([1.3, 1, 1])
            run_clicked = rc1.button(
                "▶️ Run Python against all tests", type="primary",
                use_container_width=True, key="run_py",
            )
            if rc2.button("🧹 Reset template", use_container_width=True, key="reset_py"):
                ss.user_code = ""
                ss.run_results = None
                st.rerun()
            if rc3.button("📋 Copy-paste hint", use_container_width=True, key="hint_py"):
                st.info(
                    "Tip: your function can accept either `**kwargs` or the exact "
                    "named parameters — both work. Return the value directly."
                )

            if run_clicked:
                # Step 1: silently fetch the reference solution (cached).
                # This does NOT reveal the solution to the user; we only use
                # sol.code.python as a trusted oracle to grade against.
                reference_code = ""
                if ss.is_demo:
                    reference_code = demo.SOLUTION.code.python or ""
                else:
                    try:
                        if ss.solution is None:
                            ss.solution = tutor.solve(ss.problem)
                        reference_code = (ss.solution.code.python if ss.solution else "") or ""
                    except tutor.NeedsClarification as e:
                        st.warning(f"🤔 {e}")
                        st.info("Grading will only use the visible example cases until you add more details.")
                    except Exception as e:
                        st.warning(
                            f"Couldn't fetch reference solution ({e}). "
                            "Grading only against the visible example cases."
                        )

                # Step 2: if non-demo and we have a reference, generate+validate
                # hidden test cases now (LLM inputs only; expected computed by
                # running the reference).
                if not ss.is_demo and reference_code:
                    try:
                        with st.spinner("Generating hidden test cases (validated against the reference solution)…"):
                            validated = tests_gen.generate(
                                ss.problem,
                                meta.examples or [],
                                reference_code,
                                n=30,
                                visible=3,
                            )
                        if validated:
                            ss.test_cases = validated
                    except Exception as e:
                        st.warning(f"Test generator failed ({e}) — using only visible examples.")

                cases = ss.test_cases or []
                if not cases:
                    st.warning("No test cases available for this problem yet.")
                else:
                    with st.spinner(f"Running your Python against {len(cases)} test cases…"):
                        fn, results = code_runner.run_cases(
                            ss.user_code, cases, timeout=10.0,
                        )
                    ss.run_fn = fn
                    ss.run_results = results
                    ss.active_lang = "python"
                    st.rerun()

            # ----- Compact summary under the editor (Problem 2) -----
            if ss.run_results and ss.active_lang == "python":
                passed = sum(1 for r in ss.run_results if r.ok)
                total = len(ss.run_results)
                ok_all = passed == total and total > 0
                bg = "rgba(52,211,153,.12)" if ok_all else "rgba(248,113,113,.10)"
                bd = "#34d399" if ok_all else "#f87171"
                ico = "✅" if ok_all else "❌"
                st.markdown(
                    f'<div style="background:{bg};border:1px solid {bd};'
                    f'border-radius:10px;padding:12px 16px;margin:12px 0;">'
                    f'<div style="display:flex;gap:10px;align-items:center;">'
                    f'<div style="font-size:24px;">{ico}</div>'
                    f'<div style="flex:1;color:#e7ecff;">'
                    f'<b style="font-size:16px;">{passed} / {total} test cases passed</b> '
                    f'<span style="color:#9aa6cf;">· entry: <code>{ss.run_fn}</code></span>'
                    f'</div></div></div>',
                    unsafe_allow_html=True,
                )

                # Show FIRST failing case inline, full details in Tests tab.
                first_fail = next((r for r in ss.run_results if not r.ok), None)
                if first_fail:
                    case = (ss.test_cases or [])[first_fail.idx] if first_fail.idx < len(ss.test_cases or []) else {}
                    label = case.get("label", "")
                    st.markdown(
                        f'<div style="background:rgba(248,113,113,.06);'
                        f'border-left:3px solid #f87171;border-radius:8px;'
                        f'padding:10px 14px;margin:6px 0 10px;">'
                        f'<div style="color:#fca5a5;font-weight:700;font-size:13px;'
                        f'letter-spacing:.04em;">❌ First failing case · #{first_fail.idx + 1} — {label}</div>'
                        f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                        f'color:#e7ecff;margin-top:6px;">'
                        f'<div><span style="color:#9aa6cf;">Input:</span> {first_fail.inp}</div>'
                        f'<div><span style="color:#9aa6cf;">Expected:</span> '
                        f'<span style="color:#6ee7b7;">{first_fail.expected}</span></div>'
                        f'<div><span style="color:#9aa6cf;">Got:</span> '
                        f'<span style="color:#fca5a5;">{first_fail.got}</span></div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                    if first_fail.stderr:
                        st.caption("Error:")
                        st.code(first_fail.stderr, language="text")
                    st.caption(
                        f"Open the **🧪 Tests** tab to see every failing case with full details."
                    )

        # ----- Java -----------------------------------------------------
        with lang_tabs[1]:
            available = lang_status["java"]["available"]
            if not ss.user_code_java:
                # Problem-aware starter: if we have a cached solution, use its
                # Java code as the starting point so the editor isn't showing
                # stale Two Sum boilerplate for a different problem.
                ref_java = ""
                if ss.is_demo:
                    ref_java = demo.SOLUTION.code.java or ""
                elif ss.solution and ss.solution.code.java:
                    ref_java = ss.solution.code.java
                if ref_java:
                    ss.user_code_java = ref_java
                else:
                    ss.user_code_java = (
                        "import java.util.*;\n\n"
                        f"// Problem: {meta.title or 'your problem'}\n"
                        "// TODO: implement your solution.\n"
                        "class Solution {\n"
                        "    // Rename this method to match the expected signature\n"
                        "    // from the problem statement.\n"
                        "    public Object solve(/* parameters */) {\n"
                        "        return null;\n"
                        "    }\n"
                        "}\n"
                    )
            if _HAS_ACE:
                val = st_ace(
                    value=ss.user_code_java, language="java", theme="dracula",
                    keybinding="vscode", font_size=15, tab_size=4,
                    show_gutter=True, show_print_margin=False, wrap=False,
                    auto_update=True, min_lines=28, max_lines=46, key="ace_java",
                )
                ss.user_code_java = val or ss.user_code_java
            else:
                ss.user_code_java = st.text_area(
                    "Java code", value=ss.user_code_java, height=560,
                    key="code_java_ta", label_visibility="collapsed",
                )
            st.warning(
                "☕ **Java is a reference editor only right now** — code typed here is "
                "NOT executed. Only the 🐍 Python tab runs against the test suite. "
                "Use this tab to review or practise the Java syntax alongside your "
                "Python solution. Live Java grading is on the roadmap."
                + ("" if available else "\n\n_(No `javac`/`java` was detected on your PATH, so enabling it would also need a compiler install.)_")
            )

        # ----- C++ ------------------------------------------------------
        with lang_tabs[2]:
            available = lang_status["cpp"]["available"]
            if not ss.user_code_cpp:
                ref_cpp = ""
                if ss.is_demo:
                    ref_cpp = demo.SOLUTION.code.cpp or ""
                elif ss.solution and ss.solution.code.cpp:
                    ref_cpp = ss.solution.code.cpp
                if ref_cpp:
                    ss.user_code_cpp = ref_cpp
                else:
                    ss.user_code_cpp = (
                        "#include <bits/stdc++.h>\n"
                        "using namespace std;\n\n"
                        f"// Problem: {meta.title or 'your problem'}\n"
                        "// TODO: implement your solution.\n"
                        "class Solution {\n"
                        "public:\n"
                        "    // Rename this method and signature to match the problem.\n"
                        "    auto solve(/* parameters */) {\n"
                        "        return 0;\n"
                        "    }\n"
                        "};\n"
                    )
            if _HAS_ACE:
                val = st_ace(
                    value=ss.user_code_cpp, language="c_cpp", theme="dracula",
                    keybinding="vscode", font_size=15, tab_size=4,
                    show_gutter=True, show_print_margin=False, wrap=False,
                    auto_update=True, min_lines=28, max_lines=46, key="ace_cpp",
                )
                ss.user_code_cpp = val or ss.user_code_cpp
            else:
                ss.user_code_cpp = st.text_area(
                    "C++ code", value=ss.user_code_cpp, height=560,
                    key="code_cpp_ta", label_visibility="collapsed",
                )
            st.warning(
                "⚡ **C++ is a reference editor only right now** — code typed here is "
                "NOT executed. Only the 🐍 Python tab runs against the test suite. "
                "Use this tab to review or practise the C++ syntax alongside your "
                "Python solution. Live C++ grading is on the roadmap."
                + ("" if available else "\n\n_(No `g++`/`clang++` was detected on your PATH.)_")
            )

    # =================== TAB 3 — TESTS =================================
    with t_tests:
        st.markdown("##### 🧪 Test suite")
        if tc_hidden_n == 0 and not ss.is_demo:
            st.caption(
                f"**{len(tc_visible)} visible** example case(s) loaded from the "
                "problem statement. **Extra hidden cases are generated and "
                "validated** against a trusted reference solution the first time "
                "you click *Run Python* — so no test ever has a fabricated "
                "expected value."
            )
        else:
            st.caption(
                f"**{len(tc_visible)} visible** examples shown below. "
                f"**{tc_hidden_n} hidden** cases cover edge conditions "
                f"(duplicates, negatives, zeros, extremes, large n). "
                "Each hidden case's expected output is verified by running a "
                "trusted reference solution — so no test has a fabricated answer."
            )

        for i, c in enumerate(tc_visible, 1):
            st.markdown(
                f'<div class="cs-sim">'
                f'<div style="color:#9aa6cf;font-size:11px;font-weight:800;'
                f'letter-spacing:.08em;text-transform:uppercase;">Visible case {i}</div>'
                f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                f'color:#e7ecff;margin-top:6px;"><b>Input:</b> {c.get("input_label","")}</div>'
                f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                f'color:#6ee7b7;"><b>Expected:</b> {c.get("expected")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if tc_hidden_n:
            st.markdown(
                f'<div class="cs-follow">🔒 <b>{tc_hidden_n} hidden test cases</b> — '
                f'revealed only after you run your code. Just like a real online judge.'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ----- Run results (from last Run-Python click) -----
        if ss.run_results:
            passed = sum(1 for r in ss.run_results if r.ok)
            total = len(ss.run_results)
            ok_all = passed == total and total > 0
            head_bg = "rgba(52,211,153,.15)" if ok_all else "rgba(248,113,113,.12)"
            head_bd = "#34d399" if ok_all else "#f87171"
            head_ico = "✅" if ok_all else "❌"
            head_txt = ("All tests passed! You can proceed to the full walkthrough."
                        if ok_all else
                        f"Passed {passed} · Failed {total - passed}. Fix the failures below.")
            st.markdown(
                f'<div style="background:{head_bg};border:1px solid {head_bd};'
                f'border-radius:10px;padding:12px 16px;margin:12px 0;'
                f'display:flex;gap:10px;align-items:center;">'
                f'<div style="font-size:26px;">{head_ico}</div>'
                f'<div style="flex:1;color:#e7ecff;">'
                f'<b style="font-size:16px;">{passed} / {total} passed</b> '
                f'<span style="color:#9aa6cf;">— entry: <code>{ss.run_fn}</code>, lang: {ss.active_lang}</span><br>'
                f'<span style="color:#c9d2f5;font-size:13px;">{head_txt}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Split fail-first, then visible, then hidden passes folded.
            failed = [r for r in ss.run_results if not r.ok]
            passed_list = [r for r in ss.run_results if r.ok]

            if failed:
                st.markdown(f"##### ❌ Failing cases ({len(failed)})")
                for r in failed[:20]:
                    case = (ss.test_cases or [])[r.idx] if r.idx < len(ss.test_cases or []) else {}
                    label = case.get("label", "")
                    with st.expander(
                        f"❌ #{r.idx + 1} {label} — {r.duration_ms} ms",
                        expanded=True,
                    ):
                        st.markdown(
                            f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                            f'color:#e7ecff;border-left:3px solid #f87171;padding-left:10px;">'
                            f'<div><span style="color:#9aa6cf;">Input:</span> {r.inp}</div>'
                            f'<div><span style="color:#9aa6cf;">Expected:</span> '
                            f'<span style="color:#6ee7b7;">{r.expected}</span></div>'
                            f'<div><span style="color:#9aa6cf;">Got:</span> '
                            f'<span style="color:#fca5a5;">{r.got}</span></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if r.stderr:
                            st.markdown("**Error:**")
                            st.code(r.stderr, language="text")
                        if r.stdout:
                            st.markdown("**stdout:**")
                            st.code(r.stdout, language="text")
                if len(failed) > 20:
                    st.caption(f"(+ {len(failed) - 20} more failing cases hidden)")

            if passed_list:
                with st.expander(f"✅ Passed cases ({len(passed_list)})", expanded=False):
                    for r in passed_list[:40]:
                        case = (ss.test_cases or [])[r.idx] if r.idx < len(ss.test_cases or []) else {}
                        label = case.get("label", "")
                        st.markdown(
                            f'- ✅ #{r.idx + 1} *{label}* · `{r.duration_ms} ms`'
                        )
                    if len(passed_list) > 40:
                        st.caption(f"(+ {len(passed_list) - 40} more)")

    # =================== TAB 4 — NOTES =================================
    with t_notes:
        st.markdown("##### ✍️ Describe your approach (optional)")
        st.caption(
            "Interviewers ask you to explain your plan BEFORE you code. "
            "Write 1-3 sentences here to commit to an idea."
        )
        approach = st.text_area(
            "Your approach", value=ss.approach, height=140,
            key="approach_input", label_visibility="collapsed",
        )
        ss.approach = approach

        st.markdown("##### 🎯 Suggested flow")
        st.markdown(
            "1. **Read** the problem + examples in the 📝 tab.\n"
            "2. **Write** a 1-line plan here.\n"
            "3. **Code** your solution in the 💻 editor.\n"
            "4. **Run** against all tests in the 🧪 tab.\n"
            "5. Unlock **hints** if stuck, or jump to the **animated walkthrough** "
            "once you've solved (or want to compare)."
        )

    # ---------------- Nav bar (below the tabs) ----------------
    st.markdown("---")
    all_passed = bool(ss.run_results) and all(r.ok for r in ss.run_results)
    can_unlock = bool(ss.approach.strip()) or remaining == 0 or all_passed

    colx, coly, colz, colw = st.columns([1.4, 1, 1, 1])
    unlock_label = ("🎉 All tests passed — show walkthrough"
                    if all_passed else "🔓 I'm ready — unlock hints")
    if colx.button(unlock_label, disabled=not can_unlock, type="primary"):
        ss.stage = "solved" if all_passed else "hints"
        st.rerun()
    if coly.button("💡 Just give me hints"):
        ss.stage = "hints"
        st.rerun()
    if colz.button("⏩ Skip to solution"):
        ss.stage = "solved"
        st.rerun()
    if colw.button("↩ Back"):
        ss.stage = "intake"
        st.rerun()

    # Auto-tick timer only when user hasn't started typing anywhere — Streamlit
    # can't detect typing, so we only tick if there's no code & no results yet.
    if remaining > 0 and not ss.run_results and not ss.user_code.strip():
        time.sleep(1)
        st.rerun()

# ---------------------------------------------------------------------------
# Stage: HINTS
# ---------------------------------------------------------------------------
elif ss.stage == "hints":
    st.markdown("### 3️⃣ Hint ladder")
    st.caption("4 progressive hints. Reveal only what you need.")

    for i, h in enumerate(ss.hint_texts, start=1):
        st.success(f"**Hint {i}/4** — {h}")

    if ss.hints_shown < 4:
        if st.button(f"💡 Reveal hint {ss.hints_shown + 1}"):
            level = ss.hints_shown + 1
            with st.spinner(f"Thinking of hint {level}…"):
                if ss.is_demo:
                    from core.tutor import _offline_hint
                    h = _offline_hint(level)
                else:
                    try:
                        h = tutor.hint(ss.problem, level, approach=ss.approach)
                    except Exception as e:
                        h = f"(hint unavailable: {e})"
            ss.hint_texts.append(h)
            ss.hints_shown = level
            st.rerun()
    else:
        st.info("All 4 hints revealed.")

    colp, colq = st.columns([1, 1])
    if colp.button("✅ I got it — show full solution", type="primary"):
        ss.stage = "solved"
        st.rerun()
    if colq.button("↩ Back to editor"):
        ss.stage = "think"
        st.rerun()

# ---------------------------------------------------------------------------
# Stage: SOLVED (teach)
# ---------------------------------------------------------------------------
elif ss.stage == "solved":
    if ss.solution is None:
        with st.spinner("Generating solution…"):
            try:
                ss.solution = tutor.solve(ss.problem)
            except tutor.NeedsClarification as e:
                st.warning(f"🤔 {e}")
                with st.form("clarify_form"):
                    extra = st.text_area(
                        "Tell me more about the problem",
                        placeholder="Example:\nInput: nums = [2,7,11,15], target = 9\nOutput: [0,1]\n\nConstraints: 2 <= n <= 10^4",
                        height=160,
                    )
                    submitted = st.form_submit_button("🔁 Try again with this info", type="primary")
                if submitted and extra.strip():
                    ss.problem = ss.problem.rstrip() + "\n\n--- Additional info from user ---\n" + extra.strip()
                    ss.solution = None
                    ss.meta = None
                    st.rerun()
                st.stop()
            except Exception as e:
                st.error(f"Could not generate solution: {e}")
                st.stop()

    sol: Solution = ss.solution
    meta: ProblemMeta = ss.meta or ProblemMeta()

    if ss.frames is None:
        with st.spinner("Building animation frames…"):
            try:
                ss.frames = tutor.frames(ss.problem, sol, lang=lang)
            except Exception:
                ss.frames = FrameScript()

    frames: FrameScript = ss.frames

    if not ss.audio_map and frames.frames:
        with st.spinner(
            f"Synthesising flowing Hindi narration ({len(frames.frames)} segments)…"
        ):
            try:
                stitched, ends, per = animator.build_narration_track(
                    frames, speaker=voice, lang=lang
                )
                ss.audio_map = per
                ss.stitched_uri = stitched
                ss.frame_ends = ends
            except Exception:
                ss.audio_map = {}
                ss.stitched_uri = ""
                ss.frame_ends = []

    st.markdown(f"### 4️⃣ {sol.approach_name}")
    st.write(sol.intuition)

    # ---- Plain-English problem explanation ------------------------------
    if getattr(sol, "problem_explanation", ""):
        st.markdown(
            f'<div class="cs-card" style="margin:10px 0 14px 0;'
            f'background:linear-gradient(135deg,#1a2547,#172040);'
            f'border-left:4px solid #7c9cff;padding:14px 16px;">'
            f'<div style="font-size:13px;font-weight:800;color:#a8b8ff;'
            f'letter-spacing:.4px;margin-bottom:6px;">💡 WHAT THIS PROBLEM IS ASKING</div>'
            f'<div style="color:#dde4ff;line-height:1.65;font-size:14px;">'
            f'{sol.problem_explanation}</div></div>',
            unsafe_allow_html=True,
        )

    # ---- Per-test-case walkthroughs (input → output → why) --------------
    walkthroughs = getattr(sol, "example_walkthroughs", []) or []
    if walkthroughs:
        st.markdown("**🧭 Test cases — explained step by step**")
        for i, w in enumerate(walkthroughs, 1):
            st.markdown(
                f'<div class="cs-card" style="margin-bottom:10px;padding:12px 14px;'
                f'border-left:3px solid #5dd2a5;">'
                f'<div style="color:#9aa6cf;font-size:12px;font-weight:700;'
                f'letter-spacing:.3px;">CASE {i}</div>'
                f'<div style="font-family:ui-monospace,monospace;font-size:13px;'
                f'margin-top:6px;color:#dde4ff;">'
                f'<b style="color:#7c9cff;">Input:</b> {w.input}<br>'
                f'<b style="color:#5dd2a5;">Output:</b> {w.output}'
                f'</div>'
                + (f'<div style="margin-top:8px;color:#c9d2f5;font-size:13px;'
                   f'line-height:1.6;"><b style="color:#ffd479;">Why:</b> '
                   f'{w.explanation}</div>' if w.explanation else "")
                + '</div>',
                unsafe_allow_html=True,
            )

    # ---- Problem card (title / description / examples / constraints) -----
    _title = meta.title or "Problem"
    _diff = (meta.difficulty or "").lower()
    _diff_cls = {"easy": "cs-diff-easy", "medium": "cs-diff-medium",
                 "hard": "cs-diff-hard"}.get(_diff, "cs-diff-medium")
    _header = (
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">'
        f'<div style="font-size:18px;font-weight:800;">📝 {_title}</div>'
        + (f'<span class="{_diff_cls}">{meta.difficulty}</span>' if meta.difficulty else "")
        + (f'<span class="cs-chip" style="margin:0;">{meta.topic}</span>' if meta.topic else "")
        + '</div>'
    )
    st.markdown(f'<div class="cs-card" style="margin-bottom:14px;">{_header}'
                f'<div style="color:#c9d2f5;line-height:1.55;font-size:14px;">'
                f'{meta.description or ss.problem}</div></div>',
                unsafe_allow_html=True)

    if meta.examples or meta.constraints:
        ex_col, co_col = st.columns([1.2, 1])
        with ex_col:
            if meta.examples:
                st.markdown("**Examples**")
                for i, ex in enumerate(meta.examples, 1):
                    st.markdown(
                        f'<div class="cs-card" style="margin-bottom:8px;padding:12px 14px;">'
                        f'<div style="color:#9aa6cf;font-size:12px;font-weight:700;">Example {i}</div>'
                        f'<div style="font-family:ui-monospace,monospace;font-size:13px;margin-top:6px;">'
                        f'<b>Input:</b> {ex.input}<br>'
                        f'<b>Output:</b> {ex.output}'
                        + (f'<br><span style="color:#9aa6cf;"><b>Explanation:</b> {ex.explanation}</span>'
                           if ex.explanation else "")
                        + '</div></div>',
                        unsafe_allow_html=True,
                    )
        with co_col:
            if meta.constraints:
                st.markdown("**Constraints**")
                items = "".join(f"<li>{c}</li>" for c in meta.constraints)
                st.markdown(
                    f'<div class="cs-card" style="padding:12px 14px;">'
                    f'<ul style="margin:0;padding-left:18px;font-size:13px;'
                    f'font-family:ui-monospace,monospace;color:#c9d2f5;line-height:1.7;">'
                    f'{items}</ul></div>',
                    unsafe_allow_html=True,
                )

    # Company chips
    if sol.companies:
        chips = "".join(f'<span class="cs-chip">🏢 {c}</span>' for c in sol.companies)
        st.markdown(
            f'<div class="cs-card" style="margin-bottom:14px;">'
            f'<div style="color:#9aa6cf;font-size:12px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;margin-bottom:8px;">Asked at</div>{chips}</div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns([1.2, 1])

    with left:
        tabs = st.tabs([
            f"📋 Steps ({len(sol.steps)})",
            "💻 Code",
            f"🔍 Dry run ({len(sol.dry_run)})",
            "⚙️ Complexity",
            f"⚠️ Pitfalls ({len(sol.pitfalls)})",
            f"🔀 Alternatives ({len(sol.alternatives)})",
        ])

        # ---- STEPS -----------------------------------------------------------
        with tabs[0]:
            st.markdown("##### Step-by-step algorithm")
            st.caption("Each step is one clear decision the algorithm makes.")
            if sol.steps:
                for i, s in enumerate(sol.steps, 1):
                    st.markdown(
                        f'<div class="cs-step">'
                        f'<div class="cs-step-num">{i}</div>'
                        f'<div class="cs-step-body">{s}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No step breakdown available.")

        # ---- CODE ------------------------------------------------------------
        with tabs[1]:
            st.markdown("##### Reference implementation")
            st.caption(
                "Switch language tabs below. Each implementation is minimal — "
                "focus is on the algorithm, not defensive boilerplate."
            )
            lang_tabs = st.tabs(["🐍 Python", "☕ Java", "⚡ C++"])
            with lang_tabs[0]:
                st.code(sol.code.python or "# (not available)", language="python")
                if sol.code.python:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.download_button(
                            "⬇️ Download .py",
                            data=sol.code.python,
                            file_name=f"{(meta.title or 'solution').lower().replace(' ', '_')}.py",
                            mime="text/x-python",
                        )
            with lang_tabs[1]:
                st.code(sol.code.java or "// (not available)", language="java")
            with lang_tabs[2]:
                st.code(sol.code.cpp or "// (not available)", language="cpp")

        # ---- DRY RUN ---------------------------------------------------------
        with tabs[2]:
            st.markdown("##### Line-by-line trace")
            st.caption(
                "Follow the execution on the sample input. Each line shows what "
                "happens at one iteration — exactly what you'd write on the whiteboard "
                "during an interview."
            )
            if sol.dry_run:
                for line in sol.dry_run:
                    st.markdown(
                        f'<div class="cs-dry">{line}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No dry run available.")

        # ---- COMPLEXITY ------------------------------------------------------
        with tabs[3]:
            st.markdown("##### Complexity analysis")
            tc_col, sc_col = st.columns(2)
            with tc_col:
                st.markdown(
                    f'<div class="cs-card" style="padding:16px 18px;">'
                    f'<div style="color:#9aa6cf;font-size:11px;font-weight:800;'
                    f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px;">'
                    f'⏱️ Time complexity</div>'
                    f'<div class="cs-big-o">{sol.time_complexity.big_o}</div>'
                    f'<div style="margin-top:12px;color:#c9d2f5;font-size:14px;line-height:1.6;">'
                    f'{sol.time_complexity.why}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with sc_col:
                st.markdown(
                    f'<div class="cs-card" style="padding:16px 18px;">'
                    f'<div style="color:#9aa6cf;font-size:11px;font-weight:800;'
                    f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px;">'
                    f'💾 Space complexity</div>'
                    f'<div class="cs-big-o">{sol.space_complexity.big_o}</div>'
                    f'<div style="margin-top:12px;color:#c9d2f5;font-size:14px;line-height:1.6;">'
                    f'{sol.space_complexity.why}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with st.expander("📖 Big-O cheat sheet — where this sits"):
                st.markdown(
                    "| Class | Example | Feels like |\n"
                    "|---|---|---|\n"
                    "| **O(1)** | Hash lookup, array index | Instant |\n"
                    "| **O(log n)** | Binary search, balanced tree | Very fast |\n"
                    "| **O(n)** | Single pass over array | Fast |\n"
                    "| **O(n log n)** | Efficient sort (merge/heap) | Acceptable |\n"
                    "| **O(n²)** | Nested loop, brute-force pairs | Slow for n > 10⁴ |\n"
                    "| **O(2ⁿ)** | Unmemoised recursion (Fib, subsets) | Avoid for n > 30 |\n"
                    "| **O(n!)** | Permutations | Only tiny n |"
                )

        # ---- PITFALLS --------------------------------------------------------
        with tabs[4]:
            st.markdown("##### Common mistakes & edge cases")
            st.caption(
                "What interviewers watch for. Mentioning these proactively shows "
                "senior-level thinking."
            )
            if sol.pitfalls:
                for p in sol.pitfalls:
                    st.markdown(
                        f'<div class="cs-pit">'
                        f'<div class="cs-pit-ico">⚠️</div>'
                        f'<div class="cs-pit-body">{p}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No pitfalls listed.")

        # ---- ALTERNATIVES ----------------------------------------------------
        with tabs[5]:
            st.markdown("##### Alternative approaches & trade-offs")
            st.caption(
                "Knowing these lets you defend your choice when the interviewer asks "
                "\"*why this and not that?*\""
            )
            if sol.alternatives:
                for a in sol.alternatives:
                    st.markdown(
                        f'<div class="cs-alt">'
                        f'<div class="cs-alt-head">'
                        f'<span class="cs-alt-name">🔀 {a.name}</span>'
                        f'<span class="cs-alt-bigo">{a.big_o or "—"}</span>'
                        f'</div>'
                        f'<div class="cs-alt-trade">{a.tradeoff}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No alternatives listed.")

    with right:
        st.markdown("#### 🎤 How to explain in interview")
        if sol.interview_tips:
            for t in sol.interview_tips:
                st.markdown(f'<div class="cs-tip">{t}</div>', unsafe_allow_html=True)
        else:
            st.caption("No tips available.")

    # -----------------------------------------------------------------------
    # FULL-WIDTH ANIMATION (below, bigger)
    # -----------------------------------------------------------------------
    st.markdown("### 🎬 Animated walkthrough")
    st.caption("Click the blue ▶ button inside the panel once to unlock audio. "
               "Use Prev / Next / Speed to control the pace.")
    if frames.frames:
        html = animator.render_html(
            frames,
            ss.audio_map,
            stitched_uri=ss.get("stitched_uri", ""),
            frame_ends=ss.get("frame_ends", []),
        )
        components.html(html, height=920, scrolling=True)

        if ss.audio_map:
            with st.expander("🔊 Per-step audio (backup players — tap if animation audio is blocked)"):
                import base64 as _b64
                for f in frames.frames:
                    src = ss.audio_map.get(str(f.id))
                    if not src:
                        continue
                    st.markdown(
                        f"**Step {f.id + 1}** — {f.annotation_hi or f.annotation_en}"
                    )
                    header, b64data = src.split(",", 1)
                    mime = header.split(";")[0].replace("data:", "")
                    st.audio(_b64.b64decode(b64data), format=mime)
        else:
            st.caption("⚠️ Using browser voice (Sarvam key missing or rate-limited).")
    else:
        st.info("Animation not available for this problem yet.")

    # -----------------------------------------------------------------------
    # Interview prep section — follow-ups + similar
    # -----------------------------------------------------------------------
    st.divider()
    st.markdown("### 🎤 Interview prep")

    st.markdown("#### ❓ Likely follow-up questions")
    if sol.followups:
        for q in sol.followups:
            st.markdown(f'<div class="cs-follow">❓ {q}</div>', unsafe_allow_html=True)
    else:
        st.caption("No follow-ups available.")

    # Similar problems
    st.markdown("#### 🔗 Similar problems to practice next")
    if sol.similar_problems:
        for sp in sol.similar_problems:
            diff_cls = {
                "easy": "cs-diff-easy", "medium": "cs-diff-medium", "hard": "cs-diff-hard",
            }.get((sp.difficulty or "").lower(), "cs-diff-medium")
            title_html = (
                f'<a href="{sp.url}" target="_blank">{sp.title}</a>'
                if sp.url else f'<b>{sp.title}</b>'
            )
            st.markdown(
                f'<div class="cs-sim">{title_html} '
                f'<span class="{diff_cls}">{sp.difficulty or "—"}</span>'
                f'<div style="color:#9aa6cf;margin-top:6px;font-size:13px;">{sp.why}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No similar problems listed.")

    # -----------------------------------------------------------------------
    # Learn More — YouTube + Articles
    # -----------------------------------------------------------------------
    st.divider()
    st.markdown("### 📚 Learn more")

    # Fallback: if LLM didn't return resources, build search links from title
    from urllib.parse import quote_plus as _qp
    _q = _qp(meta.title or ss.problem[:80])
    _yt_fallback = [
        {"title": f"NeetCode — search '{meta.title or 'this problem'}'",
         "url":   f"https://www.youtube.com/@NeetCode/search?query={_q}",
         "source":"NeetCode", "why":"Clear whiteboard-style walkthrough."},
        {"title": f"take U forward (Striver) — search",
         "url":   f"https://www.youtube.com/@takeUforward/search?query={_q}",
         "source":"take U forward", "why":"Interview-focused Hindi+English explanation."},
        {"title": f"Aditya Verma — search",
         "url":   f"https://www.youtube.com/@AdityaVermaTheProgrammingLord/search?query={_q}",
         "source":"Aditya Verma", "why":"Deep-dive pattern-based teaching."},
    ]
    _art_fallback = [
        {"title": f"LeetCode — {meta.title or 'Problem'}",
         "url":   f"https://leetcode.com/problemset/?search={_q}",
         "source":"LeetCode", "why":"Problem statement + editorial + discuss."},
        {"title": f"GeeksforGeeks — search",
         "url":   f"https://www.geeksforgeeks.org/?s={_q}",
         "source":"GeeksforGeeks", "why":"Multiple approaches side-by-side."},
        {"title": f"Google — articles & blogs",
         "url":   f"https://www.google.com/search?q={_q}+DSA+explanation+article",
         "source":"Google", "why":"Catches Striver, InterviewBit, freeCodeCamp posts."},
    ]

    _yt_list = (
        [{"title": r.title, "url": r.url, "source": r.source, "why": r.why}
         for r in sol.youtube_recommendations] or _yt_fallback
    )
    _art_list = (
        [{"title": r.title, "url": r.url, "source": r.source, "why": r.why}
         for r in sol.articles] or _art_fallback
    )

    yt_col, art_col = st.columns(2)
    with yt_col:
        st.markdown("#### ▶️ YouTube recommendations")
        if not sol.youtube_recommendations:
            st.caption("LLM didn't return picks — showing curated channel searches.")
        for r in _yt_list:
            title_html = (f'<a href="{r["url"]}" target="_blank">{r["title"]}</a>'
                          if r.get("url") else f'<b>{r["title"]}</b>')
            src = f' · <span style="color:#9aa6cf;">{r["source"]}</span>' if r.get("source") else ""
            st.markdown(
                f'<div class="cs-sim">▶️ {title_html}{src}'
                f'<div style="color:#9aa6cf;margin-top:6px;font-size:13px;">{r.get("why","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with art_col:
        st.markdown("#### 📄 Articles & references")
        if not sol.articles:
            st.caption("LLM didn't return picks — showing curated site searches.")
        for r in _art_list:
            title_html = (f'<a href="{r["url"]}" target="_blank">{r["title"]}</a>'
                          if r.get("url") else f'<b>{r["title"]}</b>')
            src = f' · <span style="color:#9aa6cf;">{r["source"]}</span>' if r.get("source") else ""
            st.markdown(
                f'<div class="cs-sim">📄 {title_html}{src}'
                f'<div style="color:#9aa6cf;margin-top:6px;font-size:13px;">{r.get("why","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    nav_a, nav_b, nav_c = st.columns([1.3, 1, 1])
    if nav_a.button("↩ Back to my editor", use_container_width=True,
                    help="Return to the editor to keep working on your own solution — "
                         "your code and test results are preserved."):
        ss.stage = "think"
        st.rerun()
    if nav_b.button("💡 Revisit hints", use_container_width=True):
        ss.stage = "hints"
        st.rerun()
    if nav_c.button("🔄 Solve another problem", use_container_width=True):
        for k in ("stage", "problem", "approach", "meta", "hints_shown",
                  "hint_texts", "solution", "frames", "audio_map",
                  "stitched_uri", "frame_ends", "is_demo",
                  "user_code", "user_code_java", "user_code_cpp",
                  "run_results", "test_cases"):
            ss.pop(k, None)
        st.rerun()
