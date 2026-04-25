"""DEPRECATED: runbook rendering moved to comment-driven-doc plugin home.

Import from ``prism.scanner_plugins.parsers.comment_doc.runbook_renderer``,
or use the stable package facade ``prism.scanner_reporting`` (which
re-exports build_runbook_rows / render_runbook / render_runbook_csv).
This submodule shim is retained for one release.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "prism.scanner_reporting.runbook is deprecated; import from "
    "prism.scanner_plugins.parsers.comment_doc.runbook_renderer or use the "
    "stable prism.scanner_reporting package facade.",
    DeprecationWarning,
    stacklevel=2,
)

from prism.scanner_plugins.parsers.comment_doc.runbook_renderer import (  # noqa: E402,F401
    build_runbook_rows,
    render_runbook,
    render_runbook_csv,
)

__all__ = [
    "build_runbook_rows",
    "render_runbook",
    "render_runbook_csv",
]
