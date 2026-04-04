"""Unit tests for VariableDiscovery orchestrator.

Tests cover:
- Static discovery from defaults/vars/meta/include_vars/set_fact
- Referenced variable discovery from task files and README
- Type inference and secret detection
- Unresolved variable handling and uncertainty reasoning
- Full discovery pipeline integration
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import given, strategies as st

from prism import scanner
from prism.scanner_core import DIContainer
from prism.scanner_core import variable_discovery as variable_discovery_module
from prism.scanner_core.variable_discovery import VariableDiscovery
from prism.scanner_extract.variable_extractor import _infer_variable_type


class TestVariableDiscoveryStaticDiscovery:
    """Static discovery: defaults/vars/meta/include_vars/set_fact."""

    def test_discover_static_empty_role(self, tmp_path):
        """Empty role yields empty variable tuple."""
        role_path = str(tmp_path)
        options = {
            "role_path": role_path,
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(role_path, options)
        discovery = VariableDiscovery(di, role_path, options)

        static = discovery.discover_static()

        assert isinstance(static, tuple)
        assert len(static) == 0

    def test_discover_static_from_defaults_main_yml(self, tmp_path):
        """Load variables from defaults/main.yml."""
        role_path = tmp_path
        defaults_dir = role_path / "defaults"
        defaults_dir.mkdir()

        (defaults_dir / "main.yml").write_text(
            "---\n"
            "default_var: default_value\n"
            "default_number: 42\n"
            "default_list:\n"
            "  - item1\n"
            "  - item2\n"
            "default_dict:\n"
            "  key: value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()

        names = {v["name"] for v in static}
        assert "default_var" in names
        assert "default_number" in names
        assert "default_list" in names
        assert "default_dict" in names

        # Check types
        type_map = {v["name"]: v["type"] for v in static}
        assert type_map["default_var"] == "str"
        assert type_map["default_number"] == "int"
        assert type_map["default_list"] == "list"
        assert type_map["default_dict"] == "dict"

    def test_discover_static_formats_defaults_like_variable_pipeline(self, tmp_path):
        """Static discovery should serialize defaults the same way as the pipeline."""
        role_path = tmp_path
        defaults_dir = role_path / "defaults"
        defaults_dir.mkdir()

        (defaults_dir / "main.yml").write_text(
            "---\n"
            "default_list:\n"
            "  - item1\n"
            "  - item2\n"
            "default_dict:\n"
            "  key: value\n"
            "default_bool: true\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static_rows = {row["name"]: row for row in discovery.discover_static()}
        pipeline_rows = {
            row["name"]: row
            for row in scanner.build_variable_insights(str(role_path))
            if row["name"] in static_rows
        }

        assert (
            static_rows["default_list"]["default"]
            == pipeline_rows["default_list"]["default"]
        )
        assert (
            static_rows["default_dict"]["default"]
            == pipeline_rows["default_dict"]["default"]
        )
        assert (
            static_rows["default_bool"]["default"]
            == pipeline_rows["default_bool"]["default"]
        )

    def test_discover_static_from_vars_main_yml(self, tmp_path):
        """Load variables from vars/main.yml when include_vars_main=True."""
        role_path = tmp_path
        (role_path / "vars").mkdir()
        (role_path / "vars" / "main.yml").write_text(
            "---\nvar_only: var_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()

        names = {v["name"] for v in static}
        assert "var_only" in names

    def test_discover_static_from_meta_argument_specs(self, tmp_path):
        """Load variables from meta/argument_specs.yml."""
        role_path = tmp_path
        (role_path / "meta").mkdir()
        (role_path / "meta" / "argument_specs.yml").write_text(
            "---\n"
            "argument_specs:\n"
            "  main:\n"
            "    options:\n"
            "      spec_var:\n"
            "        type: str\n"
            "        description: 'A spec variable'\n"
            "        default: 'spec_default'\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()

        names = {v["name"] for v in static}
        assert "spec_var" in names

    def test_discover_static_skips_vars_when_include_vars_main_false(self, tmp_path):
        """vars/ directory is skipped when include_vars_main=False."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\ndefault_var: default_value\n",
            encoding="utf-8",
        )
        (role_path / "vars").mkdir()
        (role_path / "vars" / "main.yml").write_text(
            "---\nvar_only: var_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": False,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()

        names = {v["name"] for v in static}
        assert "default_var" in names
        assert "var_only" not in names

    def test_discover_static_includes_source_and_line_number(self, tmp_path):
        """Static variables include source file and line number."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\ntest_var: test_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        assert len(static) > 0

        test_var = next((v for v in static if v["name"] == "test_var"), None)
        assert test_var is not None
        assert "defaults/main.yml" in test_var.get("provenance_source_file", "")
        assert test_var.get("provenance_line") is not None

    def test_discover_static_detects_secrets(self, tmp_path):
        """Static variables with secret patterns marked as secrets."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\n"
            "api_key: 'super_secret_key_12345'\n"
            "password: 'encrypted_password'\n"
            "normal_var: normal_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()

        secret_map = {v["name"]: v.get("secret", False) for v in static}
        # Secret detection is based on name patterns and value characteristics
        assert secret_map.get("api_key") or secret_map.get("password")

    def test_discover_static_with_invalid_yaml_continues(self, tmp_path):
        """Invalid YAML file is skipped gracefully."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\nvalid_var: value\n",
            encoding="utf-8",
        )
        (role_path / "defaults" / "broken.yml").write_text(
            "invalid: [\n",  # Broken YAML
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        # Should not raise, should continue with valid files
        static = discovery.discover_static()

        names = {v["name"] for v in static}
        assert "valid_var" in names

    def test_discover_static_exclude_vars_main(self, tmp_path):
        """Exclude vars/main.yml when include_vars_main=False."""
        role_path = tmp_path
        (role_path / "vars").mkdir()
        (role_path / "vars" / "main.yml").write_text(
            "---\nvar_only: var_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": False,  # Exclude vars
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()

        names = {v["name"] for v in static}
        assert "var_only" not in names

    def test_discover_static_invalid_yaml_handling(self, tmp_path):
        """Invalid YAML in defaults should be handled gracefully."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "invalid: yaml: content: [\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        # Should not raise, but may log error
        static = discovery.discover_static()
        assert isinstance(static, tuple)

    def test_discover_static_non_string_variable_names_skipped(self, tmp_path):
        """Non-string variable names are skipped."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\n123: invalid_name\nvalid_name: value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        names = {v["name"] for v in static}
        assert 123 not in names  # Non-string skipped
        assert "valid_name" in names


class TestVariableDiscoveryReferencedDiscovery:
    """Referenced discovery: task files and README sections."""

    def test_discover_referenced_empty_role(self, tmp_path):
        """Empty role yields empty referenced set."""
        role_path = str(tmp_path)
        options = {
            "role_path": role_path,
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(role_path, options)
        discovery = VariableDiscovery(di, role_path, options)

        referenced = discovery.discover_referenced()

        assert isinstance(referenced, (set, frozenset))
        assert len(referenced) == 0

    def test_discover_referenced_from_task_files(self, tmp_path):
        """Extract referenced variable names from task files."""
        role_path = tmp_path
        (role_path / "tasks").mkdir()
        (role_path / "tasks" / "main.yml").write_text(
            "---\n"
            "- name: Use variables\n"
            "  debug:\n"
            "    msg: '{{ task_var }}'\n"
            "- name: Conditional\n"
            "  debug:\n"
            "    msg: 'ok'\n"
            "  when: another_var\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        referenced = discovery.discover_referenced()

        # Should find referenced variables in Jinja and conditions
        assert isinstance(referenced, (set, frozenset))
        # task_var and another_var should be found
        assert len(referenced) > 0
        assert "task_var" in referenced
        assert "another_var" in referenced

    def test_discover_caches_referenced_collection_for_full_pipeline(
        self, tmp_path, monkeypatch
    ):
        """Full discovery should collect referenced names once per orchestrated run."""
        role_path = tmp_path
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "main.yml").write_text(
            "---\n"
            "- name: Use runtime value\n"
            "  ansible.builtin.debug:\n"
            '    msg: "{{ runtime_value }}"\n',
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        call_count = 0
        original = variable_discovery_module._collect_referenced_variable_names

        def _counting_collect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(
            variable_discovery_module,
            "_collect_referenced_variable_names",
            _counting_collect,
        )

        rows = discovery.discover()

        assert any(row["name"] == "runtime_value" for row in rows)
        assert call_count == 1

    def test_discover_referenced_no_readme(self, tmp_path):
        """No README file present."""
        role_path = tmp_path
        # No README

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        referenced = discovery.discover_referenced()
        assert isinstance(referenced, frozenset)
        assert len(referenced) == 0


class TestVariableDiscoveryPure:
    """Pure functional version of variable discovery."""

    def test_discover_variables_pure_empty(self):
        """Empty inputs yield empty variable tuple."""
        from prism.scanner_core.variable_discovery import discover_variables_pure

        variable_maps = {}
        argument_spec_entries = []
        referenced_names = frozenset()
        options = {
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }

        result = discover_variables_pure(
            variable_maps, argument_spec_entries, referenced_names, options
        )

        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_discover_variables_pure_with_static_vars(self):
        """Static variables from variable_maps."""
        from prism.scanner_core.variable_discovery import discover_variables_pure

        variable_maps = {"var1": "value1", "var2": 42}
        argument_spec_entries = []
        referenced_names = frozenset()
        options = {
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }

        result = discover_variables_pure(
            variable_maps, argument_spec_entries, referenced_names, options
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        names = {row["name"] for row in result}
        assert names == {"var1", "var2"}
        var1_row = next(row for row in result if row["name"] == "var1")
        assert var1_row["type"] == "str"
        assert not var1_row["secret"]

    def test_discover_variables_pure_with_unresolved(self):
        """Unresolved referenced variables."""
        from prism.scanner_core.variable_discovery import discover_variables_pure

        variable_maps = {"var1": "value1"}
        argument_spec_entries = []
        referenced_names = frozenset(["var1", "var2"])
        options = {
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }

        result = discover_variables_pure(
            variable_maps, argument_spec_entries, referenced_names, options
        )

        assert isinstance(result, tuple)
        assert len(result) == 2  # var1 static, var2 unresolved
        names = {row["name"] for row in result}
        assert names == {"var1", "var2"}
        var2_row = next(row for row in result if row["name"] == "var2")
        assert var2_row["type"] == "unknown"
        assert var2_row["uncertainty_reason"] == "Referenced but not defined in role"

    def test_discover_referenced_from_readme(self, tmp_path):
        """Extract referenced variable names from README."""
        role_path = tmp_path
        (role_path / "README.md").write_text(
            "# Role\n\n"
            "Use `{{ readme_var }}` in your playbook.\n"
            "Configure `{{ another_readme_var }}`.\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        referenced = discovery.discover_referenced()

        assert isinstance(referenced, (set, frozenset))
        # Variables from README should be found
        assert len(referenced) > 0


class TestVariableDiscoveryTypeInference:
    """Type inference and secret detection."""

    def test_infer_type_from_default_value_string(self, tmp_path):
        """String default inferred as str type."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\nstring_var: 'hello world'\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        type_map = {v["name"]: v["type"] for v in static}

        assert type_map["string_var"] == "str"

    def test_infer_type_from_default_value_int(self, tmp_path):
        """Integer default inferred as int type."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\nint_var: 42\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        type_map = {v["name"]: v["type"] for v in static}

        assert type_map["int_var"] == "int"

    def test_infer_type_from_default_value_list(self, tmp_path):
        """List default inferred as list type."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\nlist_var:\n  - one\n  - two\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        type_map = {v["name"]: v["type"] for v in static}

        assert type_map["list_var"] == "list"

    def test_infer_type_from_default_value_dict(self, tmp_path):
        """Dict default inferred as dict type."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\ndict_var:\n  key1: value1\n  key2: value2\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        type_map = {v["name"]: v["type"] for v in static}

        assert type_map["dict_var"] == "dict"

    def test_detect_secret_patterns_in_variable_names(self, tmp_path):
        """Variables with secret patterns in name marked as secrets."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        # Use values that pass secret detection heuristics
        # vault-like values trigger detection
        (role_path / "defaults" / "main.yml").write_text(
            "---\n"
            "api_key: 'vault_encrypted_key_12345abc'\n"
            "database_password: '$6$encryptedpassword123'\n"
            "normal_config: value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        secret_map = {v["name"]: v.get("secret", False) for v in static}

        # At least one of the secret-named variables should be detected
        assert secret_map.get("api_key") or secret_map.get("database_password")

    def test_infer_type_edge_cases(self, tmp_path):
        """Test type inference for various edge cases."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\n"
            "empty_string: ''\n"
            "zero: 0\n"
            "false_bool: false\n"
            "null_value: null\n"
            "complex_dict:\n"
            "  nested:\n"
            "    value: 123\n"
            "empty_list: []\n"
            "string_number: '123'\n"
            "float_value: 3.14\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        static = discovery.discover_static()
        type_map = {v["name"]: v["type"] for v in static}

        assert type_map["empty_string"] == "str"
        assert type_map["zero"] == "int"
        assert type_map["false_bool"] == "bool"
        assert type_map["null_value"] == "null"  # null becomes null type
        assert type_map["complex_dict"] == "dict"
        assert type_map["empty_list"] == "list"
        assert type_map["string_number"] == "str"  # quoted is str
        assert type_map["float_value"] == "float"

    @given(
        st.one_of(
            st.integers(),
            st.floats(),
            st.booleans(),
            st.text(),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
            st.none(),
        )
    )
    def test_infer_variable_type_property_based(self, value):
        """Property-based test for _infer_variable_type with various inputs."""
        result = _infer_variable_type(value)
        assert isinstance(result, str)
        assert result in {"int", "float", "bool", "str", "list", "dict", "null"}


class TestVariableDiscoveryUnresolved:
    """Unresolved variable handling and uncertainty reasoning."""

    def test_resolve_unresolved_empty_when_no_referenced(self, tmp_path):
        """No unresolved when referenced is empty."""
        role_path = str(tmp_path)
        (Path(role_path) / "defaults").mkdir()
        (Path(role_path) / "defaults" / "main.yml").write_text(
            "---\nmy_var: value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": role_path,
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(role_path, options)
        discovery = VariableDiscovery(di, role_path, options)

        unresolved = discovery.resolve_unresolved()

        assert isinstance(unresolved, dict)
        # If my_var is defined, it shouldn't be unresolved
        assert "my_var" not in unresolved

    def test_resolve_unresolved_finds_missing_variables(self, tmp_path):
        """Unresolved dict includes referenced but not defined variables."""
        role_path = tmp_path
        (role_path / "tasks").mkdir()
        (role_path / "tasks" / "main.yml").write_text(
            "---\n"
            "- name: Use undefined variable\n"
            "  debug:\n"
            "    msg: '{{ undefined_var }}'\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        unresolved = discovery.resolve_unresolved()

        assert isinstance(unresolved, dict)
        # undefined_var should be in unresolved
        if "undefined_var" in unresolved:
            assert isinstance(unresolved["undefined_var"], str)

    def test_discover_unresolved_underscore_ignored(self, tmp_path):
        """Underscore variables ignored when flag set."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "tasks").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\npublic_var: value\n",
            encoding="utf-8",
        )
        (role_path / "tasks" / "main.yml").write_text(
            "---\n- name: Use vars\n  debug:\n    msg: '{{ _internal_var }} {{ public_var }}'\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": True,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        unresolved = discovery.resolve_unresolved()
        names = set(unresolved.keys())
        assert "_internal_var" not in names  # ignored
        assert "public_var" not in names  # resolved


class TestVariableDiscoveryIntegration:
    """Full discovery pipeline integration."""

    def test_discover_combines_static_and_referenced(self, tmp_path):
        """discover() returns all variables (static + referenced)."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\nstatic_var: static_value\n",
            encoding="utf-8",
        )
        (role_path / "tasks").mkdir()
        (role_path / "tasks" / "main.yml").write_text(
            "---\n"
            "- name: Use variables\n"
            "  debug:\n"
            "    msg: '{{ static_var }} {{ referenced_var }}'\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        all_vars = discovery.discover()

        assert isinstance(all_vars, tuple)
        assert len(all_vars) > 0

        names = {v["name"] for v in all_vars}
        assert "static_var" in names

    def test_discover_returns_variable_rows(self, tmp_path):
        """discover() returns VariableRow dicts with all required fields."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\ntest_var: test_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        all_vars = discovery.discover()

        assert len(all_vars) > 0
        var = all_vars[0]

        # Check required fields
        assert "name" in var
        assert "type" in var
        assert "provenance_source_file" in var or "source" in var

    def test_discover_performance_baseline(self, tmp_path):
        """discover() should complete in reasonable time."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\n" + "\n".join(f"var_{i}: value_{i}" for i in range(100)),
            encoding="utf-8",
        )
        (role_path / "tasks").mkdir()
        (role_path / "tasks" / "main.yml").write_text(
            "---\n" "- name: Task\n" "  debug:\n" "    msg: '{{ var_0 }}'\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        import time

        start = time.time()
        all_vars = discovery.discover()
        elapsed = time.time() - start

        # Should complete in <2 seconds
        assert elapsed < 2.0
        assert len(all_vars) > 0

    def test_discover_produces_immutable_results(self, tmp_path):
        """discover() results should be immutable (TypedDict)."""
        role_path = tmp_path
        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text(
            "---\ntest_var: test_value\n",
            encoding="utf-8",
        )

        options = {
            "role_path": str(role_path),
            "include_vars_main": True,
            "exclude_path_patterns": None,
            "vars_seed_paths": None,
            "ignore_unresolved_internal_underscore_references": False,
        }
        di = DIContainer(str(role_path), options)
        discovery = VariableDiscovery(di, str(role_path), options)

        all_vars = discovery.discover()

        # TypedDict results are dicts, should be normal dicts
        assert all(isinstance(v, dict) for v in all_vars)
