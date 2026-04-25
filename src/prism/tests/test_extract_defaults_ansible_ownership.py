"""Tests verifying Ansible default-policy classes live under the ansible plugin home."""

from __future__ import annotations

import importlib
import sys
import warnings


class TestAnsibleDefaultPolicyOwnership:
    """Ansible default-policy classes are owned by scanner_plugins.ansible."""

    def test_canonical_import_path_is_ansible(self):
        from prism.scanner_plugins.ansible.default_policies import (
            AnsibleDefaultTaskAnnotationPolicyPlugin,
            AnsibleDefaultTaskLineParsingPolicyPlugin,
            AnsibleDefaultTaskTraversalPolicyPlugin,
            AnsibleDefaultVariableExtractorPolicyPlugin,
        )

        for cls in (
            AnsibleDefaultTaskAnnotationPolicyPlugin,
            AnsibleDefaultTaskLineParsingPolicyPlugin,
            AnsibleDefaultTaskTraversalPolicyPlugin,
            AnsibleDefaultVariableExtractorPolicyPlugin,
        ):
            assert cls.__module__ == "prism.scanner_plugins.ansible.default_policies"

    def test_ansible_vocabulary_lives_under_ansible(self):
        from prism.scanner_plugins.ansible.task_vocabulary import (
            INCLUDE_VARS_KEYS,
            ROLE_INCLUDE_KEYS,
            SET_FACT_KEYS,
            TASK_INCLUDE_KEYS,
        )

        assert "include_tasks" in TASK_INCLUDE_KEYS
        assert "import_tasks" in TASK_INCLUDE_KEYS
        assert "include_role" in ROLE_INCLUDE_KEYS
        assert "import_role" in ROLE_INCLUDE_KEYS
        assert "include_vars" in INCLUDE_VARS_KEYS
        assert "set_fact" in SET_FACT_KEYS

        all_keys = (
            TASK_INCLUDE_KEYS | ROLE_INCLUDE_KEYS | INCLUDE_VARS_KEYS | SET_FACT_KEYS
        )
        assert {k for k in all_keys if "ansible.builtin" in k} == set()

    def test_ansible_plugin_superset_extends_bare_vocabulary(self):
        from prism.scanner_plugins.ansible.default_policies import (
            AnsibleDefaultTaskLineParsingPolicyPlugin,
        )
        from prism.scanner_plugins.ansible.extract_policies import (
            AnsibleTaskLineParsingPolicyPlugin,
        )

        bare = AnsibleDefaultTaskLineParsingPolicyPlugin()
        canonical = AnsibleTaskLineParsingPolicyPlugin()

        assert "ansible.builtin.include_tasks" in canonical.TASK_INCLUDE_KEYS
        assert "ansible.builtin.import_tasks" in canonical.TASK_INCLUDE_KEYS
        assert "ansible.builtin.include_role" in canonical.ROLE_INCLUDE_KEYS
        assert "ansible.builtin.import_role" in canonical.ROLE_INCLUDE_KEYS
        assert "ansible.builtin.include_vars" in canonical.INCLUDE_VARS_KEYS
        assert "ansible.builtin.set_fact" in canonical.SET_FACT_KEYS

        assert bare.TASK_INCLUDE_KEYS <= canonical.TASK_INCLUDE_KEYS
        assert bare.ROLE_INCLUDE_KEYS <= canonical.ROLE_INCLUDE_KEYS
        assert bare.INCLUDE_VARS_KEYS <= canonical.INCLUDE_VARS_KEYS
        assert bare.SET_FACT_KEYS <= canonical.SET_FACT_KEYS


class TestPoliciesShimContract:
    """Deprecated scanner_plugins.policies submodules still resolve for one release."""

    @staticmethod
    def _reimport_with_warnings(module_name: str):
        sys.modules.pop(module_name, None)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            module = importlib.import_module(module_name)
            deprecations = [
                w for w in captured if issubclass(w.category, DeprecationWarning)
            ]
        return module, deprecations

    def test_extract_defaults_shim_emits_deprecation_warning(self):
        module, deprecations = self._reimport_with_warnings(
            "prism.scanner_plugins.policies.extract_defaults"
        )
        assert deprecations, "extract_defaults shim must emit DeprecationWarning"
        assert hasattr(module, "AnsibleDefaultTaskLineParsingPolicyPlugin")

    def test_constants_shim_emits_deprecation_warning(self):
        module, deprecations = self._reimport_with_warnings(
            "prism.scanner_plugins.policies.constants"
        )
        assert deprecations, "constants shim must emit DeprecationWarning"
        assert hasattr(module, "TASK_ENTRY_RE")
        assert hasattr(module, "TASK_INCLUDE_KEYS")

    def test_annotation_parsing_shim_emits_deprecation_warning(self):
        module, deprecations = self._reimport_with_warnings(
            "prism.scanner_plugins.policies.annotation_parsing"
        )
        assert deprecations, "annotation_parsing shim must emit DeprecationWarning"
        assert hasattr(module, "extract_task_annotations_for_file")

    def test_scanner_reporting_runbook_submodule_emits_deprecation_warning(self):
        module, deprecations = self._reimport_with_warnings(
            "prism.scanner_reporting.runbook"
        )
        assert deprecations, "runbook submodule shim must emit DeprecationWarning"
        assert hasattr(module, "render_runbook")
        assert hasattr(module, "build_runbook_rows")
