import warnings

from prism.scanner_data.deprecation import deprecated
from prism.scanner_config.migration import migrate_config, rollback_config


def test_deprecated_decorator_issues_warning():
    @deprecated(
        "This function is deprecated. Use new_function instead.", version="2.0.0"
    )
    def old_function():
        return "old"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = old_function()
        assert result == "old"
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "This function is deprecated. Use new_function instead." in str(
            w[0].message
        )
        assert "version 2.0.0" in str(w[0].message)


def test_deprecated_decorator_preserves_functionality():
    @deprecated("Deprecated", version="1.0.0")
    def add(a, b):
        return a + b

    assert add(1, 2) == 3


def test_migrate_config():
    old_config = {"old_key": "value", "other_key": "existing"}
    new_config = migrate_config(old_config)
    assert "old_key" not in new_config
    assert new_config["new_key"] == "value"  # migrated
    assert new_config["other_key"] == "existing"


def test_rollback_config():
    new_config = {"new_key": "value"}
    old_config = rollback_config(new_config)
    assert "old_key" in old_config
    assert old_config["old_key"] == "value"
    assert "new_key" not in old_config
