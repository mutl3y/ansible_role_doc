"""Tests for extension registry functionality."""

import pytest
from prism.scanner_extensions.registry import ExtensionRegistry, ExtensionInterface


class MockExtension(ExtensionInterface):
    """Mock extension for testing."""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def get_name(self) -> str:
        return self.name

    def get_version(self) -> str:
        return self.version

    def execute(self, data: dict) -> dict:
        return {"result": f"executed by {self.name}"}


def test_register_and_get_extension():
    """Test registering and retrieving an extension."""
    registry = ExtensionRegistry()
    ext = MockExtension("test_ext", "1.0.0")
    registry.register(ext)

    retrieved = registry.get_extension("test_ext")
    assert retrieved is ext


def test_dynamic_loading():
    """Test dynamic loading of extensions from modules."""
    registry = ExtensionRegistry()
    registry.load_from_module("prism.tests.test_dynamic_extension")

    ext = registry.get_extension("dynamic_test")
    assert ext.get_name() == "dynamic_test"
    assert ext.get_version() == "1.0.0"
    result = ext.execute({"test": "data"})
    assert result == {"dynamic": True, "data": {"test": "data"}}


def test_version_compatibility():
    """Test version compatibility checking."""
    registry = ExtensionRegistry()
    ext = MockExtension("test_ext", "1.0.0")
    registry.register(ext)

    # Compatible
    retrieved = registry.get_extension("test_ext", required_version="^1.0.0")
    assert retrieved is ext

    # Incompatible
    with pytest.raises(ValueError):
        registry.get_extension("test_ext", required_version="^2.0.0")


def test_extension_isolation():
    """Test that extensions are isolated."""
    registry = ExtensionRegistry()
    ext1 = MockExtension("ext1", "1.0.0")
    ext2 = MockExtension("ext2", "1.0.0")
    registry.register(ext1)
    registry.register(ext2)

    assert registry.get_extension("ext1") is ext1
    assert registry.get_extension("ext2") is ext2
    # Ensure they don't interfere
    assert ext1.execute({}) != ext2.execute({})
