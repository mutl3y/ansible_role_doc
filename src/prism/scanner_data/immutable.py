"""Immutable data structures for scanner data contracts."""

from __future__ import annotations


class FrozenDict(dict):
    """Immutable dict that raises on mutation attempts."""

    def __setitem__(self, key, value):
        raise TypeError("FrozenDict is immutable")

    def __delitem__(self, key):
        raise TypeError("FrozenDict is immutable")

    def pop(self, *args, **kwargs):
        raise TypeError("FrozenDict is immutable")

    def popitem(self):
        raise AttributeError("FrozenDict is immutable")

    def clear(self):
        raise AttributeError("FrozenDict is immutable")

    def update(self, *args, **kwargs):
        raise AttributeError("FrozenDict is immutable")

    def setdefault(self, key, default=None):
        raise AttributeError("FrozenDict is immutable")


__all__ = ["FrozenDict"]
