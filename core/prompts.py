"""Prompt loader — reads versioned markdown files from /prompts and renders them."""
from __future__ import annotations

from functools import lru_cache
from jinja2 import Template

from .config import settings


@lru_cache(maxsize=32)
def _raw(name: str) -> str:
    path = settings.prompts_dir / f"{name}.md"
    return path.read_text(encoding="utf-8")


def render(name: str, **ctx) -> str:
    return Template(_raw(name)).render(**ctx)
