"""Thin wrapper around diskcache for memoising LLM + TTS responses."""
from __future__ import annotations

import hashlib
from typing import Any, Callable

import diskcache

from .config import settings

_cache = diskcache.Cache(str(settings.cache_dir))


def key(*parts: Any) -> str:
    blob = "||".join(repr(p) for p in parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def memoise(namespace: str, *parts: Any, producer: Callable[[], Any]) -> Any:
    k = f"{namespace}:{key(*parts)}"
    if k in _cache:
        return _cache[k]
    value = producer()
    _cache[k] = value
    return value


def get(k: str) -> Any:
    return _cache.get(k)


def set_(k: str, value: Any) -> None:
    _cache[k] = value
