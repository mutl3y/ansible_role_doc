"""DEPRECATED: annotation parsing moved to canonical home.

Import from ``prism.scanner_plugins.parsers.comment_doc.annotation_parsing``.
This shim is retained for one release.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "prism.scanner_plugins.policies.annotation_parsing is deprecated; "
    "import from prism.scanner_plugins.parsers.comment_doc.annotation_parsing.",
    DeprecationWarning,
    stacklevel=2,
)

from prism.scanner_plugins.parsers.comment_doc.annotation_parsing import (  # noqa: E402,F401
    annotation_payload_looks_yaml,
    extract_task_annotations_for_file,
    get_marker_line_re,
    split_task_annotation_label,
    split_task_target_payload,
    task_anchor,
)

__all__ = [
    "annotation_payload_looks_yaml",
    "extract_task_annotations_for_file",
    "get_marker_line_re",
    "split_task_annotation_label",
    "split_task_target_payload",
    "task_anchor",
]
