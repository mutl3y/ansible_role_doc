"""Ansible-backed default policy implementations.

These classes provide concrete default implementations that are currently
Ansible-specific. They delegate traversal, detection, and extraction logic
to prism.scanner_plugins.ansible.task_traversal_bare and sibling modules.
Platform-specific plugins (e.g. Kubernetes, Terraform) would provide their
own equivalents rather than extending these classes.

Implementation is decomposed across sibling modules:
- constants.py                        — key sets and regex patterns
- ansible/task_traversal_bare.py      — Ansible traversal primitives (this module's runtime)
- annotation_parsing.py               — annotation extraction
"""

from __future__ import annotations

from prism.scanner_plugins.ansible.default_policies import (
    AnsibleDefaultTaskAnnotationPolicyPlugin,
    AnsibleDefaultTaskLineParsingPolicyPlugin,
    AnsibleDefaultTaskTraversalPolicyPlugin,
    AnsibleDefaultVariableExtractorPolicyPlugin,
)
from prism.scanner_plugins.policies.constants import (
    COMMENT_CONTINUATION_RE,
    COMMENTED_TASK_ENTRY_RE,
    INCLUDE_VARS_KEYS,
    ROLE_INCLUDE_KEYS,
    SET_FACT_KEYS,
    TASK_BLOCK_KEYS,
    TASK_ENTRY_RE,
    TASK_INCLUDE_KEYS,
    TASK_META_KEYS,
    TEMPLATED_INCLUDE_RE,
    WHEN_IN_LIST_RE,
    YAML_LIKE_KEY_VALUE_RE,
    YAML_LIKE_LIST_ITEM_RE,
)
from prism.scanner_plugins.policies.constants import (
    DEFAULT_DOC_MARKER_PREFIX,
)
from prism.scanner_plugins.ansible.task_traversal_bare import (
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
from prism.scanner_plugins.parsers.comment_doc.marker_utils import (
    normalize_marker_prefix,
)
from prism.scanner_plugins.policies.annotation_parsing import (
    annotation_payload_looks_yaml,
    extract_task_annotations_for_file,
    get_marker_line_re,
    split_task_annotation_label,
    split_task_target_payload,
    task_anchor,
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
    "collect_unconstrained_dynamic_role_includes",
    "collect_unconstrained_dynamic_task_includes",
    "detect_task_module",
    "expand_include_target_candidates",
    "extract_constrained_when_values",
    "annotation_payload_looks_yaml",
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
