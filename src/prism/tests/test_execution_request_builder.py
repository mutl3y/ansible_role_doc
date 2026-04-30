"""Unit tests for scanner_core.execution_request_builder pure helpers (FIND-13 closure)."""

from __future__ import annotations

from prism.scanner_core.execution_request_builder import (
    NonCollectionRunScanExecutionRequest,
    _ScanStateBridge,
)


class TestNonCollectionRunScanExecutionRequestShape:
    def test_is_frozen_dataclass(self) -> None:
        import dataclasses

        fields = {
            f.name for f in dataclasses.fields(NonCollectionRunScanExecutionRequest)
        }
        assert fields == {
            "role_path",
            "scan_options",
            "strict_mode",
            "runtime_registry",
            "scanner_context",
            "build_payload_fn",
        }

    def test_is_immutable(self) -> None:
        import dataclasses

        @dataclasses.dataclass(frozen=True)
        class _Stub:
            pass

        assert NonCollectionRunScanExecutionRequest.__dataclass_params__.frozen  # type: ignore[attr-defined]


class TestBuildDisplayVariables:
    def _call(self, rows):
        return _ScanStateBridge._build_display_variables(tuple(rows))

    def test_empty_rows_returns_empty_dict(self) -> None:
        assert self._call([]) == {}

    def test_rows_sorted_by_name(self) -> None:
        rows = [{"name": "z_var"}, {"name": "a_var"}]
        out = self._call(rows)
        assert list(out.keys()) == ["a_var", "z_var"]

    def test_rows_with_empty_name_are_skipped(self) -> None:
        rows = [{"name": ""}, {"name": None}, {"name": "valid"}]
        out = self._call(rows)
        assert list(out.keys()) == ["valid"]

    def test_field_mapping_populates_correctly(self) -> None:
        row = {
            "name": "my_var",
            "type": "str",
            "default": "hello",
            "source": "defaults/main.yml",
            "required": True,
            "documented": True,
            "secret": False,
            "is_unresolved": False,
            "is_ambiguous": True,
            "uncertainty_reason": "templated",
        }
        out = self._call([row])
        entry = out["my_var"]
        assert entry["type"] == "str"
        assert entry["default"] == "hello"
        assert entry["required"] is True
        assert entry["documented"] is True
        assert entry["secret"] is False
        assert entry["is_ambiguous"] is True
        assert entry["uncertainty_reason"] == "templated"

    def test_missing_optional_fields_default_to_safe_values(self) -> None:
        out = self._call([{"name": "v"}])
        entry = out["v"]
        assert entry["required"] is False
        assert entry["documented"] is False
        assert entry["secret"] is False
        assert entry["is_unresolved"] is False
        assert entry["is_ambiguous"] is False
        assert entry["uncertainty_reason"] is None

    def test_duplicate_names_last_row_wins(self) -> None:
        rows = [
            {"name": "dup", "default": "first"},
            {"name": "dup", "default": "second"},
        ]
        out = self._call(rows)
        assert out["dup"]["default"] == "second"


class TestBuildRequirementsDisplay:
    def _call(self, features):
        return _ScanStateBridge._build_requirements_display(features)

    def test_no_external_collections_returns_empty_list(self) -> None:
        assert self._call({}) == []

    def test_none_sentinel_returns_empty_list(self) -> None:
        assert self._call({"external_collections": "none"}) == []

    def test_single_collection_entry(self) -> None:
        out = self._call({"external_collections": "ns.col"})
        assert out == [{"collection": "ns.col"}]

    def test_comma_separated_entries(self) -> None:
        out = self._call({"external_collections": "ns.a, ns.b, ns.c"})
        assert out == [
            {"collection": "ns.a"},
            {"collection": "ns.b"},
            {"collection": "ns.c"},
        ]

    def test_strips_surrounding_whitespace(self) -> None:
        out = self._call({"external_collections": "  ns.x  ,  ns.y  "})
        assert [e["collection"] for e in out] == ["ns.x", "ns.y"]

    def test_empty_entries_in_csv_are_skipped(self) -> None:
        out = self._call({"external_collections": "ns.a,,ns.b"})
        assert [e["collection"] for e in out] == ["ns.a", "ns.b"]
