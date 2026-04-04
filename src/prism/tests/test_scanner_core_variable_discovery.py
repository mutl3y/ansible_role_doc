"""Unit tests for scanner_core.variable_discovery module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from prism.scanner_core.di import DIContainer
from prism.scanner_core.variable_discovery import VariableDiscovery


class TestVariableDiscovery:
    """Test VariableDiscovery orchestrator."""

    @pytest.fixture
    def di_container(self):
        """Mock DI container."""
        return Mock(spec=DIContainer)

    @pytest.fixture
    def options(self):
        """Default scan options."""
        return {
            "role_path": "/test/role",
            "include_vars_main": True,
            "exclude_path_patterns": [],
            "vars_seed_paths": [],
            "ignore_unresolved_internal_underscore_references": False,
        }

    @pytest.fixture
    def discovery(self, di_container, options):
        """VariableDiscovery instance."""
        return VariableDiscovery(di_container, "/test/role", options)

    def test_init(self, di_container, options):
        """Initialize with DI container and options."""
        discovery = VariableDiscovery(di_container, "/test/role", options)
        assert discovery._di == di_container
        assert discovery._role_path == "/test/role"
        assert discovery._options == options
        assert discovery._role_root == Path("/test/role").resolve()

    @patch("prism.scanner_core.variable_discovery.load_role_variable_maps")
    @patch("prism.scanner_core.variable_discovery.iter_role_argument_spec_entries")
    @patch("prism.scanner_core.variable_discovery._collect_set_fact_names")
    def test_discover_static_empty_role(
        self, mock_set_fact, mock_arg_spec, mock_load_vars, discovery
    ):
        """Discover static variables in empty role."""
        # Mocks
        mock_load_vars.return_value = ({}, {}, {}, {})
        mock_arg_spec.return_value = []
        mock_set_fact.return_value = set()

        result = discovery.discover_static()
        assert result == ()

    @patch("prism.scanner_core.variable_discovery.load_role_variable_maps")
    @patch("prism.scanner_core.variable_discovery.iter_role_argument_spec_entries")
    @patch("prism.scanner_core.variable_discovery._collect_set_fact_names")
    def test_discover_static_defaults_only(
        self, mock_set_fact, mock_arg_spec, mock_load_vars, discovery
    ):
        """Discover static variables from defaults only."""
        # Mocks
        defaults_data = {"var1": "value1", "var2": 42}
        defaults_sources = {"var1": Path("/test/role/defaults/main.yml")}
        mock_load_vars.return_value = (defaults_data, {}, defaults_sources, {})
        mock_arg_spec.return_value = []
        mock_set_fact.return_value = set()

        result = discovery.discover_static()
        assert len(result) == 2

        # Check var1
        var1 = next(r for r in result if r["name"] == "var1")
        assert var1["type"] == "str"
        assert var1["default"] == "value1"
        assert var1["source"] == "defaults/main.yml"
        assert var1["required"] is False
        assert var1["secret"] is False
        assert var1["provenance_confidence"] == 0.95
        assert var1["is_unresolved"] is False

        # Check var2
        var2 = next(r for r in result if r["name"] == "var2")
        assert var2["type"] == "int"
        assert var2["default"] == "42"

    @patch("prism.scanner_core.variable_discovery.load_role_variable_maps")
    @patch("prism.scanner_core.variable_discovery.iter_role_argument_spec_entries")
    @patch("prism.scanner_core.variable_discovery._collect_set_fact_names")
    def test_discover_static_vars_included(
        self, mock_set_fact, mock_arg_spec, mock_load_vars, discovery
    ):
        """Discover static variables including vars when enabled."""
        # Mocks
        defaults_data = {"var1": "value1"}
        vars_data = {"var2": "value2"}
        defaults_sources = {}
        vars_sources = {"var2": Path("/test/role/vars/main.yml")}
        mock_load_vars.return_value = (
            defaults_data,
            vars_data,
            defaults_sources,
            vars_sources,
        )
        mock_arg_spec.return_value = []
        mock_set_fact.return_value = set()

        result = discovery.discover_static()
        assert len(result) == 2
        names = {r["name"] for r in result}
        assert names == {"var1", "var2"}

    @patch("prism.scanner_core.variable_discovery.load_role_variable_maps")
    @patch("prism.scanner_core.variable_discovery.iter_role_argument_spec_entries")
    @patch("prism.scanner_core.variable_discovery._collect_set_fact_names")
    def test_discover_static_vars_excluded(
        self, mock_set_fact, mock_arg_spec, mock_load_vars, discovery
    ):
        """Discover static variables excluding vars when disabled."""
        options = discovery._options.copy()
        options["include_vars_main"] = False
        discovery._options = options

        defaults_data = {"var1": "value1"}
        vars_data = {"var2": "value2"}
        mock_load_vars.return_value = (defaults_data, vars_data, {}, {})
        mock_arg_spec.return_value = []
        mock_set_fact.return_value = set()

        result = discovery.discover_static()
        assert len(result) == 1
        assert result[0]["name"] == "var1"

    @patch("prism.scanner_core.variable_discovery.load_role_variable_maps")
    @patch("prism.scanner_core.variable_discovery.iter_role_argument_spec_entries")
    @patch("prism.scanner_core.variable_discovery._collect_set_fact_names")
    def test_discover_static_argument_specs(
        self, mock_set_fact, mock_arg_spec, mock_load_vars, discovery
    ):
        """Discover static variables from argument specs."""
        mock_load_vars.return_value = ({}, {}, {}, {})
        mock_arg_spec.return_value = [
            (
                Path("/test/role/meta/argument_specs.yml"),
                "arg1",
                {"type": "str", "required": True},
            ),
            (
                Path("/test/role/meta/argument_specs.yml"),
                "arg2",
                {"type": "int", "default": 10},
            ),
        ]
        mock_set_fact.return_value = set()

        result = discovery.discover_static()
        assert len(result) == 2
        arg1 = next(r for r in result if r["name"] == "arg1")
        assert arg1["type"] == "string"
        assert arg1["required"] is True
        assert arg1["documented"] is True
        assert arg1["source"] == "meta/argument_specs"

        arg2 = next(r for r in result if r["name"] == "arg2")
        assert arg2["type"] == "int"
        assert arg2["default"] == "10"
        assert arg2["required"] is False

    @patch("prism.scanner_core.variable_discovery.load_role_variable_maps")
    @patch("prism.scanner_core.variable_discovery.iter_role_argument_spec_entries")
    @patch("prism.scanner_core.variable_discovery._collect_set_fact_names")
    def test_discover_static_set_fact(
        self, mock_set_fact, mock_arg_spec, mock_load_vars, discovery
    ):
        """Discover static variables from set_fact."""
        mock_load_vars.return_value = ({}, {}, {}, {})
        mock_arg_spec.return_value = []
        mock_set_fact.return_value = {"fact1", "fact2"}

        result = discovery.discover_static()
        assert len(result) == 2
        fact1 = next(r for r in result if r["name"] == "fact1")
        assert fact1["type"] == "dynamic"
        assert fact1["source"] == "set_fact"
        assert fact1["provenance_confidence"] == 0.7
        assert fact1["is_ambiguous"] is True

    @patch("prism.scanner_core.variable_discovery._collect_referenced_variable_names")
    def test_discover_referenced_task_files(self, mock_collect, discovery):
        """Discover referenced variables from task files."""
        mock_collect.return_value = {"var1", "var2"}
        result = discovery.discover_referenced()
        assert result == frozenset(["var1", "var2"])

    @patch("prism.scanner_core.variable_discovery._collect_referenced_variable_names")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_discover_referenced_readme(
        self, mock_read, mock_exists, mock_collect, discovery
    ):
        """Discover referenced variables from README."""
        mock_collect.return_value = {"var1"}
        mock_exists.return_value = True
        mock_read.return_value = "Use {{ var2 }} and {{ var3 }} in tasks."

        result = discovery.discover_referenced()
        assert result == frozenset(["var1", "var2", "var3"])

    @patch("prism.scanner_core.variable_discovery._collect_referenced_variable_names")
    @patch("pathlib.Path.exists")
    def test_discover_referenced_readme_missing(
        self, mock_exists, mock_collect, discovery
    ):
        """Discover referenced variables when README missing."""
        mock_collect.return_value = {"var1"}
        mock_exists.return_value = False

        result = discovery.discover_referenced()
        assert result == frozenset(["var1"])

    @patch("prism.scanner_core.variable_discovery._collect_referenced_variable_names")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_discover_referenced_readme_error(
        self, mock_read, mock_exists, mock_collect, discovery
    ):
        """Discover referenced variables when README read fails."""
        mock_collect.return_value = {"var1"}
        mock_exists.return_value = True
        mock_read.side_effect = OSError("Read error")

        result = discovery.discover_referenced()
        assert result == frozenset(["var1"])

    def test_resolve_unresolved_no_unresolved(self, discovery):
        """Resolve unresolved when all referenced are defined."""
        static_names = frozenset(["var1", "var2"])
        referenced = frozenset(["var1", "var2"])

        result = discovery.resolve_unresolved(
            static_names=static_names, referenced=referenced
        )
        assert result == {}

    def test_resolve_unresolved_with_unresolved(self, discovery):
        """Resolve unresolved variables."""
        static_names = frozenset(["var1"])
        referenced = frozenset(["var1", "var2", "_internal"])

        result = discovery.resolve_unresolved(
            static_names=static_names, referenced=referenced
        )
        assert "var2" in result
        assert "_internal" in result
        assert result["var2"] == "Similar variables found: var2"
        assert (
            result["_internal"]
            == "Similar variables found: _internal; Related variables: _internal, var1, var2"
        )

    def test_resolve_unresolved_calls_discover_if_none(self, discovery):
        """Resolve unresolved calls discover methods if not provided."""
        with patch.object(discovery, "discover_static") as mock_static, patch.object(
            discovery, "discover_referenced"
        ) as mock_ref:
            mock_static.return_value = ({"name": "var1"},)
            mock_ref.return_value = frozenset(["var1", "var2"])

            result = discovery.resolve_unresolved()
            assert "var2" in result

    def test_discover_integration(self, discovery):
        """Integration test for discover method."""
        with patch.object(discovery, "discover_static") as mock_static, patch.object(
            discovery, "discover_referenced"
        ) as mock_ref, patch.object(discovery, "resolve_unresolved") as mock_resolve:
            static_rows = ({"name": "var1", "type": "string"},)
            mock_static.return_value = static_rows
            mock_ref.return_value = frozenset(["var1", "var2"])
            mock_resolve.return_value = {"var2": "reason"}

            result = discovery.discover()
            assert len(result) == 2
            var1 = next(r for r in result if r["name"] == "var1")
            assert var1["name"] == "var1"
            var2 = next(r for r in result if r["name"] == "var2")
            assert var2["name"] == "var2"
            assert var2["is_unresolved"] is True
            assert var2["uncertainty_reason"] == "reason"

    def test_build_uncertainty_reason_underscore(self, discovery):
        """Build uncertainty reason for underscore variables."""
        reason = discovery._build_uncertainty_reason(
            "_var", referenced_names=frozenset(["_var"])
        )
        assert reason == "Similar variables found: _var; Related variables: _var"

    def test_build_uncertainty_reason_referenced(self, discovery):
        """Build uncertainty reason for referenced variables."""
        reason = discovery._build_uncertainty_reason(
            "var", referenced_names=frozenset(["var"])
        )
        assert reason == "Similar variables found: var"

    def test_build_uncertainty_reason_default(self, discovery):
        """Build uncertainty reason default case."""
        reason = discovery._build_uncertainty_reason(
            "var", referenced_names=frozenset()
        )
        assert reason == "No similar or related variables found"

    def test_discover_static_deduplicates_names(self, discovery):
        """Discover static deduplicates variable names."""
        with patch(
            "prism.scanner_core.variable_discovery.load_role_variable_maps"
        ) as mock_load, patch(
            "prism.scanner_core.variable_discovery.iter_role_argument_spec_entries"
        ) as mock_arg, patch(
            "prism.scanner_core.variable_discovery._collect_set_fact_names"
        ) as mock_set:
            # Same name in defaults and vars
            mock_load.return_value = ({"dup": "val1"}, {"dup": "val2"}, {}, {})
            mock_arg.return_value = []
            mock_set.return_value = set()

            result = discovery.discover_static()
            # Should only have one entry for 'dup'
            assert len(result) == 1
            assert result[0]["name"] == "dup"
            # Should take from defaults (first phase)
            assert result[0]["default"] == "val1"

    def test_discover_static_secret_detection(self, discovery):
        """Discover static detects secret variables."""
        with patch(
            "prism.scanner_core.variable_discovery.load_role_variable_maps"
        ) as mock_load, patch(
            "prism.scanner_core.variable_discovery.iter_role_argument_spec_entries"
        ) as mock_arg, patch(
            "prism.scanner_core.variable_discovery._collect_set_fact_names"
        ) as mock_set:
            mock_load.return_value = (
                {
                    "password": "thisisaverylongpasswordwithmixedchars123",
                    "api_key": "thisisaverylongapikeywithmixedchars123",
                },
                {},
                {},
                {},
            )
            mock_arg.return_value = []
            mock_set.return_value = set()

            result = discovery.discover_static()
            password_var = next(r for r in result if r["name"] == "password")
            assert password_var["secret"] is True
            api_var = next(r for r in result if r["name"] == "api_key")
            assert api_var["secret"] is True

    def test_discover_referenced_excludes_paths(self, discovery):
        """Discover referenced respects exclude patterns."""
        options = discovery._options.copy()
        options["exclude_path_patterns"] = ["**/test/**"]
        discovery._options = options

        with patch(
            "prism.scanner_core.variable_discovery._collect_referenced_variable_names"
        ) as mock_collect:
            mock_collect.return_value = {"var1"}
            discovery.discover_referenced()
            mock_collect.assert_called_once_with(
                "/test/role", exclude_paths=["**/test/**"]
            )

    # Total tests: 20
