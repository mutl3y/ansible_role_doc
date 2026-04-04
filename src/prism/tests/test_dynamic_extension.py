"""Test extension module for dynamic loading."""

from prism.scanner_extensions.registry import ExtensionInterface


class TestDynamicExtension(ExtensionInterface):
    """A test extension for dynamic loading."""

    def get_name(self) -> str:
        return "dynamic_test"

    def get_version(self) -> str:
        return "1.0.0"

    def execute(self, data: dict) -> dict:
        return {"dynamic": True, "data": data}


# List of extension classes in this module
extensions = [TestDynamicExtension]
