"""T3-03: Optional scan result cache.

Defines a cache backend protocol and an in-memory LRU implementation.
Cache key is computed from a content hash of role inputs plus a digest
of scan_options. Wiring into the scan pipeline is consumer-driven; this
module provides only the seam.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import OrderedDict
from typing import Any, Mapping, Protocol


class ScanCacheBackend(Protocol):
    """Backend protocol for caching completed scan results."""

    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any) -> None: ...

    def invalidate(self, key: str) -> None: ...

    def clear(self) -> None: ...


class _StatsAware(Protocol):
    """Internal protocol for cache backends that expose hit/miss counters."""

    @property
    def hits(self) -> int: ...

    @property
    def misses(self) -> int: ...


class InMemoryLRUScanCache:
    """In-memory least-recently-used :class:`ScanCacheBackend`.

    ``maxsize`` defaults to 64 entries. ``maxsize=0`` disables caching.
    """

    def __init__(self, maxsize: int = 64) -> None:
        if maxsize < 0:
            raise ValueError("maxsize must be >= 0")
        self._maxsize = maxsize
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        if self._maxsize == 0:
            self._misses += 1
            return None
        try:
            value = self._store.pop(key)
        except KeyError:
            self._misses += 1
            return None
        self._store[key] = value
        self._hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        if self._maxsize == 0:
            return
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    def __len__(self) -> int:
        return len(self._store)


def compute_scan_cache_key(
    *,
    role_content_hash: str,
    scan_options: Mapping[str, Any],
) -> str:
    """Build a stable cache key from a role content hash and scan options."""
    if not role_content_hash:
        raise ValueError("role_content_hash must not be empty")
    options_blob = json.dumps(scan_options, sort_keys=True, default=str)
    options_hash = hashlib.sha256(options_blob.encode("utf-8")).hexdigest()
    return f"{role_content_hash}:{options_hash}"


def compute_role_content_hash(role_path: str) -> str:
    """Compute a stable sha256 hash of a role directory's file tree and contents."""
    h = hashlib.sha256()
    root = os.path.abspath(role_path)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root)
            h.update(rel_path.encode("utf-8"))
            try:
                with open(abs_path, "rb") as fh:
                    h.update(fh.read())
            except OSError:
                pass
    return h.hexdigest()


def report_cache_stats(backend: _StatsAware) -> dict[str, Any]:
    """Return hit/miss stats for measurement."""
    total = backend.hits + backend.misses
    hit_rate = backend.hits / total if total > 0 else 0.0
    return {
        "hits": backend.hits,
        "misses": backend.misses,
        "total": total,
        "hit_rate_pct": round(hit_rate * 100, 1),
    }


__all__ = [
    "InMemoryLRUScanCache",
    "ScanCacheBackend",
    "compute_role_content_hash",
    "compute_scan_cache_key",
    "report_cache_stats",
]
