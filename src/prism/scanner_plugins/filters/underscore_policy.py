"""Back-compat re-export shim.

Canonical home: :mod:`prism.scanner_core.filters.underscore_policy`.

This module preserves the historical
``prism.scanner_plugins.filters.underscore_policy`` import path during the
g3 coupling cleanup. The filter is generic (not platform-specific), so its
ownership now lives in ``scanner_core.filters``; ``scanner_plugins`` should
not be a dependency of ``scanner_core``.
"""

from __future__ import annotations

from prism.scanner_core.filters.underscore_policy import (  # noqa: F401
    apply_underscore_reference_filter,
)

__all__ = ["apply_underscore_reference_filter"]
