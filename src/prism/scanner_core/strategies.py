"""Strategy patterns for pluggable scanner behaviors.

This module defines strategy interfaces and default implementations for
major scanner behaviors that can be customized or extended.
"""

from __future__ import annotations

from typing import Any, Protocol

from prism.scanner_data.contracts_variables import VariableRow


class VariableDiscoveryStrategy(Protocol):
    """Strategy interface for variable discovery behaviors."""

    def discover_static(
        self, role_path: str, options: dict[str, Any]
    ) -> tuple[VariableRow, ...]:
        """Discover static variables from defaults, vars, meta, etc."""
        ...

    def discover_referenced(
        self, role_path: str, options: dict[str, Any], readme_content: str | None = None
    ) -> frozenset[str]:
        """Discover referenced variable names from tasks, README, etc."""
        ...

    def resolve_unresolved(
        self,
        static_names: frozenset[str],
        referenced: frozenset[str],
        options: dict[str, Any],
    ) -> dict[str, str]:
        """Resolve unresolved variables and build uncertainty reasons."""
        ...


class StrategyRegistry:
    """Registry for pluggable strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, type[VariableDiscoveryStrategy]] = {}

    def _ensure_defaults(self) -> None:
        """Ensure default strategies are registered."""
        if "default" not in self._strategies:
            # Import here to avoid circular import
            from prism.scanner_core.variable_discovery import (
                DefaultVariableDiscoveryStrategy,
            )

            self._strategies["default"] = DefaultVariableDiscoveryStrategy

    def register(
        self, name: str, strategy_class: type[VariableDiscoveryStrategy]
    ) -> None:
        """Register a strategy class by name."""
        self._strategies[name] = strategy_class

    def get(self, name: str, di_container: Any = None) -> VariableDiscoveryStrategy:
        """Get an instance of the strategy by name."""
        self._ensure_defaults()
        strategy_class = self._strategies.get(name)
        if strategy_class is None:
            raise ValueError(f"Unknown strategy: {name}")
        if di_container is None:
            return strategy_class()
        # For strategies that need DI dependencies
        if name == "default":
            return strategy_class(
                data_loader=di_container.factory_data_loader(),
                discovery=di_container.factory_discovery(),
                task_parser=di_container.factory_task_parser(),
                variable_extractor=di_container.factory_variable_extractor(),
            )
        return strategy_class()

    def list_strategies(self) -> list[str]:
        """List available strategy names."""
        self._ensure_defaults()
        return list(self._strategies.keys())


# Global registry instance - lazy
_strategy_registry: StrategyRegistry | None = None


def get_strategy_registry() -> StrategyRegistry:
    """Get the global strategy registry."""
    global _strategy_registry
    if _strategy_registry is None:
        _strategy_registry = StrategyRegistry()
    return _strategy_registry
