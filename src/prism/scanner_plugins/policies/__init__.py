"""Domain-neutral default policy ownership seams for scanner plugins."""

from __future__ import annotations

from prism.scanner_plugins.parsers.jinja import JinjaAnalysisPolicyPlugin
from prism.scanner_plugins.parsers.yaml import YAMLParsingPolicyPlugin
from prism.scanner_plugins.policies.extract_defaults import (
    AnsibleDefaultTaskAnnotationPolicyPlugin,
)
from prism.scanner_plugins.policies.extract_defaults import (
    AnsibleDefaultTaskLineParsingPolicyPlugin,
)
from prism.scanner_plugins.policies.extract_defaults import (
    AnsibleDefaultTaskTraversalPolicyPlugin,
)
from prism.scanner_plugins.policies.extract_defaults import (
    AnsibleDefaultVariableExtractorPolicyPlugin,
)
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
