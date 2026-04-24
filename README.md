# CodeSensei — Hindi DSA Tutor (v0 prototype)

Interactive tutor that forces you to *think first*, then explains any DSA problem
visually with natural Indian Hindi/Hinglish voice.

## v0 scope
- Paste problem → think-first timer → hint ladder → full structured solution
- Hindi/Hinglish narration via Sarvam Bulbul v2 (fallback: browser TTS)
- Array-template animation synced with audio
- Two Sum demo works **without any API keys** (offline fixture)

## Quickstart
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then fill keys (optional for demo)
streamlit run app/main.py
```

Click **Load Two Sum demo** in the sidebar to try without keys.

## Stack
Streamlit · Gemini 2.0 Flash · Groq Llama 3.3 · Sarvam Bulbul v2 · SQLite · diskcache

## Status
Prototype. Phases 1–6 (SRS, notes export, company tags, multi-template anim, MCP
server) are planned but not yet built.
