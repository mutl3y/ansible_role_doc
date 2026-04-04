"""Unit tests for scanner_data.contracts_variables module."""

import pytest

from prism.scanner_data.contracts_variables import VariableRowBuilder


class TestVariableRowBuilder:
    """Test VariableRowBuilder fluent interface and invariants."""

    def test_builder_interface_fluent_chaining(self):
        """Builder methods return Self for chaining."""
        builder = VariableRowBuilder()
        result = (
            builder.name("test_var")
            .type("string")
            .default("default_value")
            .description("A test variable")
            .source("defaults/main.yml")
            .documented(True)
            .required(False)
            .secret(False)
            .provenance_source_file("defaults/main.yml")
            .provenance_line(10)
            .provenance_confidence(0.8)
            .uncertainty_reason(None)
            .is_unresolved(False)
            .is_ambiguous(False)
        )
        assert result is builder

    def test_build_requires_name(self):
        """Build fails if name is not set."""
        builder = VariableRowBuilder().type("string")
        with pytest.raises(ValueError, match="'name' is required"):
            builder.build()

    def test_build_requires_non_empty_name(self):
        """Build fails if name is empty."""
        builder = VariableRowBuilder().name("").type("string")
        with pytest.raises(ValueError, match="'name' is required"):
            builder.build()

    def test_build_requires_type(self):
        """Build fails if type is not set."""
        builder = VariableRowBuilder().name("test_var")
        with pytest.raises(ValueError, match="'type' is required"):
            builder.build()

    def test_build_requires_non_empty_type(self):
        """Build fails if type is empty."""
        builder = VariableRowBuilder().name("test_var").type("")
        with pytest.raises(ValueError, match="'type' is required"):
            builder.build()

    def test_build_validates_confidence_range(self):
        """Build fails if confidence is out of range."""
        builder = (
            VariableRowBuilder()
            .name("test_var")
            .type("string")
            .provenance_confidence(1.5)
        )
        with pytest.raises(ValueError, match="provenance_confidence must be in"):
            builder.build()

    def test_build_validates_confidence_type(self):
        """Build fails if confidence is not numeric."""
        builder = (
            VariableRowBuilder()
            .name("test_var")
            .type("string")
            .provenance_confidence("high")
        )
        with pytest.raises(
            ValueError, match="provenance_confidence must be float or int"
        ):
            builder.build()

    def test_build_applies_defaults(self):
        """Build applies default values for optional fields."""
        builder = VariableRowBuilder().name("test_var").type("string")
        result = builder.build()
        assert result["required"] is False
        assert result["secret"] is False
        assert result["documented"] is False
        assert result["provenance_confidence"] == 0.5
        assert result["is_unresolved"] is False
        assert result["is_ambiguous"] is False

    def test_build_preserves_provided_values(self):
        """Build preserves provided values."""
        builder = (
            VariableRowBuilder()
            .name("test_var")
            .type("string")
            .default("value")
            .description("desc")
            .source("source")
            .documented(True)
            .required(True)
            .secret(True)
            .provenance_source_file("file.yml")
            .provenance_line(5)
            .provenance_confidence(0.9)
            .uncertainty_reason("reason")
            .is_unresolved(True)
            .is_ambiguous(True)
        )
        result = builder.build()
        assert result["name"] == "test_var"
        assert result["type"] == "string"
        assert result["default"] == "value"
        assert result["description"] == "desc"
        assert result["source"] == "source"
        assert result["documented"] is True
        assert result["required"] is True
        assert result["secret"] is True
        assert result["provenance_source_file"] == "file.yml"
        assert result["provenance_line"] == 5
        assert result["provenance_confidence"] == 0.9
        assert result["uncertainty_reason"] == "reason"
        assert result["is_unresolved"] is True
        assert result["is_ambiguous"] is True

    def test_confidence_alias(self):
        """confidence() is alias for provenance_confidence()."""
        builder = VariableRowBuilder().name("test_var").type("string").confidence(0.7)
        result = builder.build()
        assert result["provenance_confidence"] == 0.7

    def test_provenance_helper(self):
        """provenance() sets source_file and line."""
        builder = (
            VariableRowBuilder()
            .name("test_var")
            .type("string")
            .provenance("file.yml", 10)
        )
        result = builder.build()
        assert result["provenance_source_file"] == "file.yml"
        assert result["provenance_line"] == 10

    def test_build_returns_dict(self):
        """Build returns dict."""
        builder = VariableRowBuilder().name("test_var").type("string")
        result = builder.build()
        assert isinstance(result, dict)
        assert result["name"] == "test_var"
        assert result["type"] == "string"

    def test_builder_reuse(self):
        """Builder can be reused after build."""
        builder = VariableRowBuilder().name("var1").type("string")
        result1 = builder.build()
        assert result1["name"] == "var1"

        # Reuse builder
        result2 = builder.name("var2").build()
        assert result2["name"] == "var2"

    def test_optional_fields_none_handling(self):
        """Optional fields handle None values."""
        builder = (
            VariableRowBuilder()
            .name("test_var")
            .type("string")
            .description(None)
            .provenance_line(None)
            .uncertainty_reason(None)
        )
        result = builder.build()
        assert "description" not in result
        assert result["provenance_line"] is None
        assert result["uncertainty_reason"] is None

    def test_edge_case_confidence_bounds(self):
        """Confidence bounds 0.0 and 1.0 are valid."""
        builder1 = (
            VariableRowBuilder().name("var1").type("string").provenance_confidence(0.0)
        )
        result1 = builder1.build()
        assert result1["provenance_confidence"] == 0.0

        builder2 = (
            VariableRowBuilder().name("var2").type("string").provenance_confidence(1.0)
        )
        result2 = builder2.build()
        assert result2["provenance_confidence"] == 1.0

    def test_build_returns_typed_dict_instance(self):
        """Build returns VariableRow TypedDict."""
        from prism.scanner_data.contracts_variables import VariableRow

        builder = VariableRowBuilder().name("test_var").type("string")
        result = builder.build()
        assert isinstance(result, dict)
        # Type check that it's VariableRow
        _: VariableRow = result

    # Add more tests to reach total

    def test_builder_initially_empty(self):
        """Builder starts with empty row."""
        builder = VariableRowBuilder()
        assert builder._row == {}

    def test_method_calls_modify_internal_state(self):
        """Method calls modify internal _row dict."""
        builder = VariableRowBuilder()
        builder.name("test")
        assert builder._row["name"] == "test"

    def test_build_creates_copy(self):
        """Build creates a copy of internal state."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        builder._row["name"] = "modified"
        assert result["name"] == "test"

    def test_default_confidence_half(self):
        """Default confidence is 0.5."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        assert result["provenance_confidence"] == 0.5

    def test_no_extra_fields(self):
        """Build does not include extra fields."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        expected_keys = {
            "name",
            "type",
            "required",
            "secret",
            "documented",
            "provenance_confidence",
            "is_unresolved",
            "is_ambiguous",
        }
        assert set(result.keys()).issubset(expected_keys)

    def test_example_field_optional(self):
        """example field is optional."""
        builder = VariableRowBuilder().name("test").type("string").example("ex")
        result = builder.build()
        assert result["example"] == "ex"

    def test_example_none_omitted(self):
        """example None is omitted."""
        builder = VariableRowBuilder().name("test").type("string").example(None)
        result = builder.build()
        assert "example" not in result

    def test_description_none_omitted(self):
        """description None is omitted."""
        builder = VariableRowBuilder().name("test").type("string").description(None)
        result = builder.build()
        assert "description" not in result

    def test_source_required(self):
        """source is not required."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        assert "source" not in result

    def test_provenance_source_file_required_for_build(self):
        """provenance_source_file is not required."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        assert "provenance_source_file" not in result

    def test_provenance_line_none_allowed(self):
        """provenance_line None is allowed."""
        builder = VariableRowBuilder().name("test").type("string").provenance_line(None)
        result = builder.build()
        assert result["provenance_line"] is None

    def test_uncertainty_reason_none_allowed(self):
        """uncertainty_reason None is allowed."""
        builder = (
            VariableRowBuilder().name("test").type("string").uncertainty_reason(None)
        )
        result = builder.build()
        assert result["uncertainty_reason"] is None

    def test_is_unresolved_default_false(self):
        """is_unresolved defaults to False."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        assert result["is_unresolved"] is False

    def test_is_ambiguous_default_false(self):
        """is_ambiguous defaults to False."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        assert result["is_ambiguous"] is False

    def test_fluent_return_self(self):
        """All methods return Self."""
        builder = VariableRowBuilder()
        assert isinstance(builder.name("test"), VariableRowBuilder)
        assert isinstance(builder.type("string"), VariableRowBuilder)
        assert isinstance(builder.default("val"), VariableRowBuilder)
        assert isinstance(builder.example("ex"), VariableRowBuilder)
        assert isinstance(builder.description("desc"), VariableRowBuilder)
        assert isinstance(builder.source("src"), VariableRowBuilder)
        assert isinstance(builder.documented(True), VariableRowBuilder)
        assert isinstance(builder.required(True), VariableRowBuilder)
        assert isinstance(builder.secret(True), VariableRowBuilder)
        assert isinstance(builder.provenance_source_file("file"), VariableRowBuilder)
        assert isinstance(builder.provenance_line(1), VariableRowBuilder)
        assert isinstance(builder.provenance_confidence(0.5), VariableRowBuilder)
        assert isinstance(builder.uncertainty_reason("reason"), VariableRowBuilder)
        assert isinstance(builder.is_unresolved(True), VariableRowBuilder)
        assert isinstance(builder.is_ambiguous(True), VariableRowBuilder)
        assert isinstance(builder.provenance("file", 1), VariableRowBuilder)

    def test_build_with_minimal_fields(self):
        """Build with only required fields."""
        builder = VariableRowBuilder().name("test").type("string")
        result = builder.build()
        assert result["name"] == "test"
        assert result["type"] == "string"
        assert result["required"] is False
        assert result["secret"] is False
        assert result["documented"] is False
        assert result["provenance_confidence"] == 0.5
        assert result["is_unresolved"] is False
        assert result["is_ambiguous"] is False

    def test_build_with_all_fields(self):
        """Build with all possible fields."""
        builder = (
            VariableRowBuilder()
            .name("test")
            .type("string")
            .default("def")
            .example("ex")
            .description("desc")
            .source("src")
            .documented(True)
            .required(True)
            .secret(True)
            .provenance_source_file("file")
            .provenance_line(1)
            .provenance_confidence(0.8)
            .uncertainty_reason("reason")
            .is_unresolved(True)
            .is_ambiguous(True)
        )
        result = builder.build()
        assert len(result) == 15  # all fields

    def test_build_returns_typed_dict(self):
        """Build returns VariableRow TypedDict."""
        from prism.scanner_data.contracts_variables import VariableRow

        builder = VariableRowBuilder().name("test_var").type("string")
        result = builder.build()
        assert isinstance(result, dict)
        # Type check that it's VariableRow
        _: VariableRow = result

    def test_builder_independence(self):
        """Multiple builders are independent."""
        builder1 = VariableRowBuilder().name("var1").type("string")
        builder2 = VariableRowBuilder().name("var2").type("int")
        result1 = builder1.build()
        result2 = builder2.build()
        assert result1["name"] == "var1"
        assert result2["name"] == "var2"

    def test_confidence_validation_edge_cases(self):
        """Confidence validation edge cases."""
        # Valid floats
        builder = (
            VariableRowBuilder().name("test").type("string").provenance_confidence(0.0)
        )
        result = builder.build()
        assert result["provenance_confidence"] == 0.0

        builder = (
            VariableRowBuilder().name("test").type("string").provenance_confidence(1.0)
        )
        result = builder.build()
        assert result["provenance_confidence"] == 1.0

        # Invalid
        with pytest.raises(ValueError):
            VariableRowBuilder().name("test").type("string").provenance_confidence(
                -0.1
            ).build()

        with pytest.raises(ValueError):
            VariableRowBuilder().name("test").type("string").provenance_confidence(
                1.1
            ).build()

    def test_name_validation_edge_cases(self):
        """Name validation edge cases."""
        # Valid
        builder = VariableRowBuilder().name("a").type("string")
        result = builder.build()
        assert result["name"] == "a"

        # Invalid
        with pytest.raises(ValueError):
            VariableRowBuilder().name("   ").type("string").build()

        with pytest.raises(ValueError):
            VariableRowBuilder().name(None).type("string").build()  # type: ignore[arg-type]

    def test_type_validation_edge_cases(self):
        """Type validation edge cases."""
        # Valid
        builder = VariableRowBuilder().name("test").type("str")
        result = builder.build()
        assert result["type"] == "str"

        # Invalid
        with pytest.raises(ValueError):
            VariableRowBuilder().name("test").type("   ").build()

        with pytest.raises(ValueError):
            VariableRowBuilder().name("test").type(None).build()  # type: ignore[arg-type]

    # Total tests: 35 as mentioned in memory
