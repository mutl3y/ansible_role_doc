"""
Extension registry for Prism scanner plugins.

Provides dynamic loading, version compatibility, and isolation for plugins.
Plugins are loaded from entry points or configuration and cached for performance.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Type

from prism.scanner_plugins.interfaces import (
    CommentDrivenDocumentationPlugin,
    FeatureDetectionPlugin,
    OutputOrchestrationPlugin,
    ScanPipelinePlugin,
    VariableDiscoveryPlugin,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing scanner plugins."""

    def __init__(self) -> None:
        self._variable_discovery_plugins: Dict[str, Type[VariableDiscoveryPlugin]] = {}
        self._feature_detection_plugins: Dict[str, Type[FeatureDetectionPlugin]] = {}
        self._output_orchestration_plugins: Dict[
            str, Type[OutputOrchestrationPlugin]
        ] = {}
        self._scan_pipeline_plugins: Dict[str, Type[ScanPipelinePlugin]] = {}
        self._comment_driven_doc_plugins: Dict[
            str, Type[CommentDrivenDocumentationPlugin]
        ] = {}
        self._loaded_plugins: Dict[str, Any] = {}

    def register_variable_discovery_plugin(
        self, name: str, plugin_class: Type[VariableDiscoveryPlugin]
    ) -> None:
        """Register a variable discovery plugin."""
        self._variable_discovery_plugins[name] = plugin_class
        logger.info(f"Registered variable discovery plugin: {name}")

    def register_feature_detection_plugin(
        self, name: str, plugin_class: Type[FeatureDetectionPlugin]
    ) -> None:
        """Register a feature detection plugin."""
        self._feature_detection_plugins[name] = plugin_class
        logger.info(f"Registered feature detection plugin: {name}")

    def register_output_orchestration_plugin(
        self, name: str, plugin_class: Type[OutputOrchestrationPlugin]
    ) -> None:
        """Register an output orchestration plugin."""
        self._output_orchestration_plugins[name] = plugin_class
        logger.info(f"Registered output orchestration plugin: {name}")

    def register_scan_pipeline_plugin(
        self, name: str, plugin_class: Type[ScanPipelinePlugin]
    ) -> None:
        """Register a scan pipeline plugin."""
        self._scan_pipeline_plugins[name] = plugin_class
        logger.info(f"Registered scan pipeline plugin: {name}")

    def register_comment_driven_doc_plugin(
        self, name: str, plugin_class: Type[CommentDrivenDocumentationPlugin]
    ) -> None:
        """Register a comment-driven documentation plugin."""
        self._comment_driven_doc_plugins[name] = plugin_class
        logger.info(f"Registered comment-driven documentation plugin: {name}")

    def get_variable_discovery_plugin(
        self, name: str
    ) -> Optional[Type[VariableDiscoveryPlugin]]:
        """Get a variable discovery plugin by name."""
        return self._variable_discovery_plugins.get(name)

    def get_feature_detection_plugin(
        self, name: str
    ) -> Optional[Type[FeatureDetectionPlugin]]:
        """Get a feature detection plugin by name."""
        return self._feature_detection_plugins.get(name)

    def get_output_orchestration_plugin(
        self, name: str
    ) -> Optional[Type[OutputOrchestrationPlugin]]:
        """Get an output orchestration plugin by name."""
        return self._output_orchestration_plugins.get(name)

    def get_scan_pipeline_plugin(self, name: str) -> Optional[Type[ScanPipelinePlugin]]:
        """Get a scan pipeline plugin by name."""
        return self._scan_pipeline_plugins.get(name)

    def get_comment_driven_doc_plugin(
        self, name: str
    ) -> Optional[Type[CommentDrivenDocumentationPlugin]]:
        """Get a comment-driven documentation plugin by name."""
        return self._comment_driven_doc_plugins.get(name)

    def list_variable_discovery_plugins(self) -> List[str]:
        """List all registered variable discovery plugin names."""
        return list(self._variable_discovery_plugins.keys())

    def list_feature_detection_plugins(self) -> List[str]:
        """List all registered feature detection plugin names."""
        return list(self._feature_detection_plugins.keys())

    def list_output_orchestration_plugins(self) -> List[str]:
        """List all registered output orchestration plugin names."""
        return list(self._output_orchestration_plugins.keys())

    def list_scan_pipeline_plugins(self) -> List[str]:
        """List all registered scan pipeline plugin names."""
        return list(self._scan_pipeline_plugins.keys())

    def list_comment_driven_doc_plugins(self) -> List[str]:
        """List all registered comment-driven documentation plugin names."""
        return list(self._comment_driven_doc_plugins.keys())

    def load_plugin_from_module(self, module_name: str, class_name: str) -> Any:
        """Dynamically load a plugin class from a module."""
        if module_name in self._loaded_plugins:
            return self._loaded_plugins[module_name]

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            self._loaded_plugins[module_name] = plugin_class
            logger.info(f"Loaded plugin {class_name} from {module_name}")
            return plugin_class
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load plugin {class_name} from {module_name}: {e}")
            raise


# Global registry instance
plugin_registry = PluginRegistry()
