"""Plugin name resolution, route carrier building, and preflight invocation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from prism.errors import PrismRuntimeError
from prism.scanner_kernel.scan_payload_helpers import (
    _build_routing_metadata,
    _merge_routing_metadata,
)


_ROUTING_MODE_PLUGIN = "scan_pipeline_plugin"


@dataclass(frozen=True, slots=True)
class RoutePreflightRuntimeCarrier:
    """Explicit carrier for selected route, preflight result, and runtime metadata."""

    plugin_name: str
    preflight_context: dict[str, Any]
    routing: dict[str, Any]


def resolve_scan_pipeline_plugin_class(
    *,
    registry: Any,
    plugin_name: str,
) -> Any | None:
    """Resolve a scan-pipeline plugin class from a registry."""
    return registry.get_scan_pipeline_plugin(plugin_name)


def execute_scan_pipeline_plugin(
    *,
    plugin_class: Any,
    scan_options: dict[str, Any],
    scan_context: dict[str, Any],
) -> Any:
    """Instantiate and execute a scan-pipeline plugin."""
    plugin_instance = plugin_class()
    return plugin_instance.process_scan_pipeline(
        scan_options=dict(scan_options),
        scan_context=dict(scan_context),
    )


def _resolve_default_scan_pipeline_plugin_name(registry: Any) -> str:
    list_plugins = getattr(registry, "list_scan_pipeline_plugins", None)
    get_plugin = getattr(registry, "get_scan_pipeline_plugin", None)

    if callable(list_plugins):
        registered = [
            name for name in list_plugins() if isinstance(name, str) and name.strip()
        ]
        if "default" in registered:
            return "default"
        if len(registered) == 1:
            return registered[0]
        if registered:
            return sorted(registered)[0]

    if callable(get_plugin):
        if get_plugin("default") is not None:
            return "default"

    raise PrismRuntimeError(
        code="scan_pipeline_default_unavailable",
        category="runtime",
        message="no scan-pipeline plugin default is registered",
        detail={"registry_type": type(registry).__name__},
    )


def _resolve_policy_context_scan_pipeline_plugin_name(
    scan_options: dict[str, Any],
) -> str | None:
    policy_context = scan_options.get("policy_context")
    if not isinstance(policy_context, dict):
        return None

    selection_context = policy_context.get("selection")
    if not isinstance(selection_context, dict):
        return None

    plugin_name = selection_context.get("plugin")
    if not isinstance(plugin_name, str) or not plugin_name.strip():
        return None

    return plugin_name.strip()


def _is_explicitly_selected_plugin_name(scan_options: dict[str, Any]) -> bool:
    configured = scan_options.get("scan_pipeline_plugin")
    if isinstance(configured, str) and configured.strip():
        return True
    if _resolve_policy_context_scan_pipeline_plugin_name(scan_options) is not None:
        return True
    platform = scan_options.get("platform")
    if isinstance(platform, str) and platform.strip():
        return True
    return False


def resolve_scan_pipeline_plugin_name(
    *,
    scan_options: dict[str, Any],
    registry: Any | None = None,
) -> str:
    """Resolve the scan-pipeline plugin selector from canonical scan options."""
    configured = scan_options.get("scan_pipeline_plugin")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()

    configured_from_policy = _resolve_policy_context_scan_pipeline_plugin_name(
        scan_options
    )
    if configured_from_policy is not None:
        return configured_from_policy

    platform = scan_options.get("platform")
    if isinstance(platform, str) and platform.strip():
        return platform.strip()

    if registry is None:
        raise ValueError("registry must be provided for plugin name resolution")
    return _resolve_default_scan_pipeline_plugin_name(registry)


def _build_route_preflight_runtime_carrier(
    *,
    plugin_name: str,
    plugin_context: dict[str, Any] | None,
) -> RoutePreflightRuntimeCarrier:
    preflight_context = dict(plugin_context) if isinstance(plugin_context, dict) else {}
    preflight_context.setdefault("plugin_name", plugin_name)
    routing = _merge_routing_metadata(
        preflight_context.get("routing"),
        _build_routing_metadata(
            mode=_ROUTING_MODE_PLUGIN,
            selected_plugin=plugin_name,
            include_selection_order=True,
        ),
    )
    preflight_context["routing"] = routing
    return RoutePreflightRuntimeCarrier(
        plugin_name=plugin_name,
        preflight_context=preflight_context,
        routing=routing,
    )


def _invoke_kernel_orchestrator(
    *,
    kernel_orchestrator_fn: Callable[..., dict[str, Any]],
    role_path: str,
    scan_options: dict[str, Any],
    route_preflight_runtime: RoutePreflightRuntimeCarrier,
) -> dict[str, Any]:
    return kernel_orchestrator_fn(
        role_path=role_path,
        scan_options=scan_options,
        route_preflight_runtime=route_preflight_runtime,
    )
