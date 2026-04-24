"""Hindi/Hinglish TTS with Sarvam Bulbul v2 as primary, browser fallback flag.

Returns audio bytes (WAV/MP3) suitable for `st.audio`.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx

from . import cache
from .config import settings

SARVAM_URL = "https://api.sarvam.ai/text-to-speech"


@dataclass
class TTSResult:
    audio_bytes: bytes | None      # None means "use browser fallback"
    mime: str                      # "audio/wav" | "audio/mpeg" | ""
    provider: str                  # "sarvam" | "browser"
    text: str


def synth(text: str, *, speaker: str | None = None, lang: str = "hi-IN") -> TTSResult:
    """Synthesize speech. Falls back to browser-TTS signal if Sarvam unavailable."""
    text = (text or "").strip()
    if not text:
        return TTSResult(None, "", "browser", "")

    speaker = speaker or settings.default_voice

    if settings.has_sarvam:
        try:
            return _sarvam(text, speaker=speaker, lang=lang)
        except Exception:  # pragma: no cover - network edge
            pass
    return TTSResult(None, "", "browser", text)


def _sarvam(text: str, *, speaker: str, lang: str) -> TTSResult:
    ck = f"sarvam2:{cache.key(text, speaker, lang, settings.sarvam_model)}"
    cached = cache.get(ck)
    if cached is not None:
        return TTSResult(cached, "audio/wav", "sarvam", text)

    payload = {
        "inputs": [text[:900]],  # Sarvam per-chunk limit
        "target_language_code": lang,
        "speaker": speaker,
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
        "model": settings.sarvam_model,
        # Teacher-like delivery: slightly slower pace, natural pitch.
        "pace": 0.95,
        "pitch": 0.0,
        "loudness": 1.2,
    }
    headers = {"api-subscription-key": settings.sarvam_api_key}
    with httpx.Client(timeout=30) as client:
        r = client.post(SARVAM_URL, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    b64 = data["audios"][0]
    audio = base64.b64decode(b64)
    cache.set_(ck, audio)
    return TTSResult(audio, "audio/wav", "sarvam", text)
