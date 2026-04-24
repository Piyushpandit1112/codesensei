# Deploying CodeSensei — Free Tier

## Recommended: Streamlit Community Cloud (100% free, native fit)

**What you get:** 1 GB RAM, public URL, free SSL, secrets manager, CI from GitHub. No credit card.

### One-time setup

1. **Push this repo to GitHub** (public OR private — Streamlit can read both).

   ```powershell
   git init
   git add .
   git commit -m "Initial CodeSensei deploy"
   git branch -M main
   git remote add origin https://github.com/<your-username>/codesensei.git
   git push -u origin main
   ```

2. **Verify these files are in the repo** (already created for you):
   - `requirements.txt` — Python deps
   - `runtime.txt` — pins Python 3.11
   - `packages.txt` — apt deps (empty)
   - `.streamlit/config.toml` — dark theme + headless server
   - `.gitignore` — keeps `.env` and `secrets.toml` OUT

3. **Sign in at [share.streamlit.io](https://share.streamlit.io)** with the same GitHub account → **New app**.

4. Fill in:
   - Repository: `<you>/codesensei`
   - Branch: `main`
   - Main file path: `app/main.py`
   - App URL (subdomain): pick whatever you want.

5. Click **Advanced settings → Secrets** and paste:

   ```toml
   GROQ_API_KEY   = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   GEMINI_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   SARVAM_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

   (At minimum you need ONE of GROQ or GEMINI. Sarvam is optional — without it the app still works, audio narration will be silent.)

6. Click **Deploy**. First build takes 2-3 min.

### Updating

Every `git push` to `main` redeploys automatically. Edits to secrets via the Streamlit dashboard hot-reload without a rebuild.

---

## Backup option: Hugging Face Spaces (also free)

If Streamlit Cloud rejects you:

1. Create a Space → SDK = **Streamlit**.
2. Push the same repo to the Space's git remote.
3. In Space **Settings → Variables and secrets**, add the same three keys.
4. Done.

Hugging Face gives you 16 GB RAM on free CPU spaces — overkill for this app but useful if Streamlit Cloud throttles.

---

## What runs locally vs on the cloud

| Feature | Local Windows | Streamlit Cloud (Linux) |
|---|---|---|
| Streamlit UI | ✅ | ✅ |
| Groq + Gemini calls | ✅ | ✅ |
| Sarvam TTS narration | ✅ | ✅ |
| Python user-code grading (subprocess) | ✅ | ✅ |
| Java reference editor | ✅ (no exec) | ✅ (no exec) |
| C++ reference editor | ✅ (no exec) | ✅ (no exec) |
| Disk cache | `.codesensei_cache/` | `/tmp/codesensei_cache/` (resets per deploy) |

---

## Troubleshooting

**"ModuleNotFoundError: streamlit_ace"** → `requirements.txt` wasn't picked up. Check the file is at repo root (not under any subfolder).

**App boots but shows "Demo mode"** → API keys missing/typo'd in Streamlit secrets.

**429 / quota errors** → the app already auto-fails over Groq → Gemini. If both quotas are exhausted you're stuck until the rate-limit window resets.

**Audio missing** → Sarvam key absent or that endpoint is down. The app continues without narration.

**"Read-only filesystem" on cache** → already handled; the app falls back to `/tmp`.

---

## Cost reminder

- Streamlit Community Cloud: **free forever** for public projects with ≤1 GB RAM.
- Groq free tier: ~30 requests / min, ~14 400 tokens / min for `llama-3.3-70b-versatile`.
- Gemini free tier: 15 RPM, 1 500 RPD for `gemini-2.0-flash`.
- Sarvam: free credits then paid — see your dashboard.

For a personal demo / portfolio piece this combo costs **₹0**.
