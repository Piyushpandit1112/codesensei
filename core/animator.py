"""Build the embeddable animator HTML with frame script + audio injected.

Generates ONE continuous narration track (all frames stitched together) so
playback sounds like a real teacher speaking in flow — not robotic per-frame
chunks with gaps. Frame visuals advance when the audio's currentTime crosses
per-frame boundaries.
"""
from __future__ import annotations

import base64
import io
import json
import wave
from concurrent.futures import ThreadPoolExecutor

from .config import settings
from .schemas import FrameScript
from .tts import synth


def _silence_wav(ref_wav: bytes, ms: int) -> bytes:
    """Generate a tiny silent WAV matching the reference's params."""
    with wave.open(io.BytesIO(ref_wav), "rb") as w:
        nch, sw, fr = w.getnchannels(), w.getsampwidth(), w.getframerate()
    n = int(fr * (ms / 1000.0))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(nch); w.setsampwidth(sw); w.setframerate(fr)
        w.writeframes(b"\x00" * (n * nch * sw))
    return out.getvalue()


def _concat_wavs(wavs: list[bytes], *, join_gap_ms: int = 140) -> tuple[bytes, list[float]]:
    """Concatenate WAVs; return (stitched_bytes, per_clip_end_time_seconds)."""
    if not wavs:
        return b"", []
    with wave.open(io.BytesIO(wavs[0]), "rb") as w0:
        nch, sw, fr = w0.getnchannels(), w0.getsampwidth(), w0.getframerate()
    gap = _silence_wav(wavs[0], join_gap_ms) if join_gap_ms > 0 else b""
    gap_data = b""
    gap_nframes = 0
    if gap:
        with wave.open(io.BytesIO(gap), "rb") as wg:
            gap_data = wg.readframes(wg.getnframes())
            gap_nframes = wg.getnframes()
    out = io.BytesIO()
    cum: list[float] = []
    total_frames = 0
    with wave.open(out, "wb") as wout:
        wout.setnchannels(nch); wout.setsampwidth(sw); wout.setframerate(fr)
        for i, w in enumerate(wavs):
            with wave.open(io.BytesIO(w), "rb") as wi:
                wout.writeframes(wi.readframes(wi.getnframes()))
                total_frames += wi.getnframes()
            cum.append(total_frames / fr)     # end of this clip (visual switch point)
            if i < len(wavs) - 1 and gap_data:
                wout.writeframes(gap_data)
                total_frames += gap_nframes
    return out.getvalue(), cum


def build_narration_track(
    frames: FrameScript, *, speaker: str, lang: str
) -> tuple[str, list[float], dict[str, str]]:
    """Build one stitched narration + per-frame end timestamps.

    Returns: (stitched_data_uri_or_empty, [end_time_s_per_frame], per_frame_uris)
    """
    jobs = [(i, (f.annotation_hi or f.annotation_en or "").strip())
            for i, f in enumerate(frames.frames)]

    def _one(job):
        idx, text = job
        if not text:
            return idx, None
        try:
            res = synth(text, speaker=speaker, lang="hi-IN")
            if res.audio_bytes and res.mime.startswith("audio/wav"):
                return idx, res.audio_bytes
        except Exception:
            pass
        return idx, None

    per_frame_bytes: list[bytes | None] = [None] * len(jobs)
    with ThreadPoolExecutor(max_workers=4) as ex:
        for idx, wb in ex.map(_one, jobs):
            per_frame_bytes[idx] = wb

    per_frame_uris: dict[str, str] = {}
    for i, wb in enumerate(per_frame_bytes):
        if wb:
            b64 = base64.b64encode(wb).decode("ascii")
            per_frame_uris[str(i)] = f"data:audio/wav;base64,{b64}"

    # Need every clip for clean stitch; else fall back to per-frame mode.
    if not all(per_frame_bytes):
        return "", [], per_frame_uris

    stitched, cum = _concat_wavs([wb for wb in per_frame_bytes if wb], join_gap_ms=140)
    if not stitched:
        return "", [], per_frame_uris
    b64 = base64.b64encode(stitched).decode("ascii")
    return f"data:audio/wav;base64,{b64}", cum, per_frame_uris


# Backward-compat shim used by some callers.
def build_audio_map(frames: FrameScript, *, speaker: str, lang: str) -> dict[str, str]:
    _uri, _cum, per = build_narration_track(frames, speaker=speaker, lang=lang)
    return per


def render_html(
    frames: FrameScript,
    audio_map: dict[str, str],
    *,
    stitched_uri: str = "",
    frame_ends: list[float] | None = None,
) -> str:
    template = (settings.assets_dir / "animator.html").read_text(encoding="utf-8")
    html = template.replace("__FRAME_SCRIPT__", json.dumps(frames.model_dump()))
    html = html.replace("__AUDIO_MAP__", json.dumps(audio_map))
    html = html.replace("__STITCHED_URI__", json.dumps(stitched_uri))
    html = html.replace("__FRAME_ENDS__", json.dumps(frame_ends or []))
    return html
