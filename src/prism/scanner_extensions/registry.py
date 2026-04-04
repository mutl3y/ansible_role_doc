"""Extension registry for dynamic loading and management of scanner capabilities."""

from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from typing import Dict, Optional


class ExtensionInterface(ABC):
    """Interface that all extensions must implement."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the extension name."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return the extension version as string."""
        pass

    @abstractmethod
    def execute(self, data: dict) -> dict:
        """Execute the extension with given data."""
        pass


class ExtensionRegistry:
    """Registry for managing scanner extensions with dynamic loading and version compatibility."""

    def __init__(self):
        self._extensions: Dict[str, ExtensionInterface] = {}

    def register(self, extension: ExtensionInterface) -> None:
        """Register an extension in the registry."""
        name = extension.get_name()
        if name in self._extensions:
            raise ValueError(f"Extension '{name}' already registered")
        self._extensions[name] = extension

    def get_extension(
        self, name: str, required_version: Optional[str] = None
    ) -> ExtensionInterface:
        """Retrieve an extension by name, optionally checking version compatibility."""
        if name not in self._extensions:
            raise ValueError(f"Extension '{name}' not found")

        ext = self._extensions[name]
        if required_version:
            if not self._is_version_compatible(ext.get_version(), required_version):
                raise ValueError(
                    f"Extension '{name}' version {ext.get_version()} does not satisfy {required_version}"
                )

        return ext

    def load_from_module(self, module_path: str) -> None:
        """Dynamically load extensions from a module path."""
        try:
            module = importlib.import_module(module_path)
            # Assume the module has an 'extensions' list
            if hasattr(module, "extensions"):
                for ext_class in module.extensions:
                    ext = ext_class()
                    self.register(ext)
        except ImportError as e:
            raise ValueError(f"Failed to load module '{module_path}': {e}")

    def list_extensions(self) -> list[str]:
        """List all registered extension names."""
        return list(self._extensions.keys())

    def _is_version_compatible(self, ext_version: str, required: str) -> bool:
        """Simple version compatibility check. Assumes semantic versions."""
        # For simplicity, check if major version matches for ^required
        if required.startswith("^"):
            req_base = required[1:]
            req_major = req_base.split(".")[0]
            ext_major = ext_version.split(".")[0]
            return req_major == ext_major
        # Exact match
        return ext_version == required
