"""Domain-neutral default policy ownership seams for scanner plugins.

The Ansible default-policy classes re-exported here are kept for backward
compatibility for one release; canonical homes are under
``prism.scanner_plugins.ansible``.
"""

from __future__ import annotations

from prism.scanner_plugins.ansible.default_policies import (
    AnsibleDefaultTaskAnnotationPolicyPlugin,
    AnsibleDefaultTaskLineParsingPolicyPlugin,
    AnsibleDefaultTaskTraversalPolicyPlugin,
    AnsibleDefaultVariableExtractorPolicyPlugin,
)
from prism.scanner_plugins.parsers.jinja import JinjaAnalysisPolicyPlugin
from prism.scanner_plugins.parsers.yaml import YAMLParsingPolicyPlugin
from prism.scanner_plugins.policies.default_scan_pipeline import (
    DefaultScanPipelinePlugin,
)

__all__ = [
    "DefaultScanPipelinePlugin",
    "AnsibleDefaultTaskAnnotationPolicyPlugin",
    "AnsibleDefaultTaskLineParsingPolicyPlugin",
    "AnsibleDefaultTaskTraversalPolicyPlugin",
    "AnsibleDefaultVariableExtractorPolicyPlugin",
    "JinjaAnalysisPolicyPlugin",
    "YAMLParsingPolicyPlugin",
]
