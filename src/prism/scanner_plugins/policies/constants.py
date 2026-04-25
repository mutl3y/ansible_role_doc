"""DEPRECATED: re-exports moved to canonical homes.

This module is a compatibility shim retained for one release. New code must
import from:

- Ansible YAML vocabulary -> ``prism.scanner_plugins.ansible.task_vocabulary``
- Ansible-syntax regex    -> ``prism.scanner_plugins.ansible.task_regex``
- YAML line-shape regex   -> ``prism.scanner_plugins.parsers.yaml.line_shape``
- Marker utilities        -> ``prism.scanner_plugins.parsers.comment_doc.marker_utils``
"""

from __future__ import annotations

import warnings

warnings.warn(
    "prism.scanner_plugins.policies.constants is deprecated; import from "
    "prism.scanner_plugins.ansible.task_vocabulary, "
    "prism.scanner_plugins.ansible.task_regex, "
    "prism.scanner_plugins.parsers.yaml.line_shape, or "
    "prism.scanner_plugins.parsers.comment_doc.marker_utils.",
    DeprecationWarning,
    stacklevel=2,
)

from prism.scanner_plugins.ansible.task_regex import (  # noqa: E402,F401
    TEMPLATED_INCLUDE_RE,
    WHEN_IN_LIST_RE,
)
from prism.scanner_plugins.ansible.task_vocabulary import (  # noqa: E402,F401
    INCLUDE_VARS_KEYS,
    ROLE_INCLUDE_KEYS,
    SET_FACT_KEYS,
    TASK_BLOCK_KEYS,
    TASK_INCLUDE_KEYS,
    TASK_META_KEYS,
)
from prism.scanner_plugins.parsers.comment_doc.marker_utils import (  # noqa: E402,F401
    COMMENT_CONTINUATION_RE,
    DEFAULT_DOC_MARKER_PREFIX,
)
from prism.scanner_plugins.parsers.yaml.line_shape import (  # noqa: E402,F401
    COMMENTED_TASK_ENTRY_RE,
    TASK_ENTRY_RE,
    YAML_LIKE_KEY_VALUE_RE,
    YAML_LIKE_LIST_ITEM_RE,
)

__all__ = [
    "COMMENT_CONTINUATION_RE",
    "COMMENTED_TASK_ENTRY_RE",
    "DEFAULT_DOC_MARKER_PREFIX",
    "INCLUDE_VARS_KEYS",
    "ROLE_INCLUDE_KEYS",
    "SET_FACT_KEYS",
    "TASK_BLOCK_KEYS",
    "TASK_ENTRY_RE",
    "TASK_INCLUDE_KEYS",
    "TASK_META_KEYS",
    "TEMPLATED_INCLUDE_RE",
    "WHEN_IN_LIST_RE",
    "YAML_LIKE_KEY_VALUE_RE",
    "YAML_LIKE_LIST_ITEM_RE",
]
