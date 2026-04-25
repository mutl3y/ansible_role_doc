"""DEPRECATED: Ansible default-policy plugins moved to canonical home.

Import from ``prism.scanner_plugins.ansible.default_policies``. This shim
is retained for one release.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "prism.scanner_plugins.policies.extract_defaults is deprecated; import "
    "from prism.scanner_plugins.ansible.default_policies (classes) and "
    "prism.scanner_plugins.ansible.task_vocabulary / "
    "prism.scanner_plugins.ansible.task_regex / "
    "prism.scanner_plugins.parsers.yaml.line_shape (constants).",
    DeprecationWarning,
    stacklevel=2,
)

from prism.scanner_plugins.ansible.default_policies import (  # noqa: E402,F401
    AnsibleDefaultTaskAnnotationPolicyPlugin,
    AnsibleDefaultTaskLineParsingPolicyPlugin,
    AnsibleDefaultTaskTraversalPolicyPlugin,
    AnsibleDefaultVariableExtractorPolicyPlugin,
)
from prism.scanner_plugins.ansible.task_regex import (  # noqa: E402,F401
    TEMPLATED_INCLUDE_RE,
    WHEN_IN_LIST_RE,
)
from prism.scanner_plugins.ansible.task_traversal_bare import (  # noqa: E402,F401
    collect_unconstrained_dynamic_role_includes,
    collect_unconstrained_dynamic_task_includes,
    detect_task_module,
    expand_include_target_candidates,
    extract_constrained_when_values,
    iter_dynamic_role_include_targets,
    iter_role_include_targets,
    iter_task_include_edges,
    iter_task_include_targets,
    iter_task_mappings,
)
from prism.scanner_plugins.ansible.task_vocabulary import (  # noqa: E402,F401
    INCLUDE_VARS_KEYS,
    ROLE_INCLUDE_KEYS,
    SET_FACT_KEYS,
    TASK_BLOCK_KEYS,
    TASK_INCLUDE_KEYS,
    TASK_META_KEYS,
)
from prism.scanner_plugins.parsers.comment_doc.annotation_parsing import (  # noqa: E402,F401
    annotation_payload_looks_yaml,
    extract_task_annotations_for_file,
    get_marker_line_re,
    split_task_annotation_label,
    split_task_target_payload,
    task_anchor,
)
from prism.scanner_plugins.parsers.comment_doc.marker_utils import (  # noqa: E402,F401
    COMMENT_CONTINUATION_RE,
    DEFAULT_DOC_MARKER_PREFIX,
    normalize_marker_prefix,
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
    "AnsibleDefaultTaskAnnotationPolicyPlugin",
    "AnsibleDefaultTaskLineParsingPolicyPlugin",
    "AnsibleDefaultTaskTraversalPolicyPlugin",
    "AnsibleDefaultVariableExtractorPolicyPlugin",
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
    "annotation_payload_looks_yaml",
    "collect_unconstrained_dynamic_role_includes",
    "collect_unconstrained_dynamic_task_includes",
    "detect_task_module",
    "expand_include_target_candidates",
    "extract_constrained_when_values",
    "extract_task_annotations_for_file",
    "get_marker_line_re",
    "iter_dynamic_role_include_targets",
    "iter_role_include_targets",
    "iter_task_include_edges",
    "iter_task_include_targets",
    "iter_task_mappings",
    "normalize_marker_prefix",
    "split_task_annotation_label",
    "split_task_target_payload",
    "task_anchor",
]
