"""Runtime Protocol contracts for DI factories and orchestrator boundary surfaces.

Replaces weak `Callable[..., Any]` aliases at the scanner_core ↔ scanner_kernel
boundary. Each Protocol documents the contract that previously had to be inferred
from call sites.
"""

from __future__ import annotations

from typing import Any, Protocol


class PluginLoader(Protocol):
    """Loads a plugin instance by platform name (kernel-side seam)."""

    def __call__(self, platform: str) -> Any: ...


class KernelOrchestrator(Protocol):
    """Invokes the kernel orchestration entrypoint with keyword args."""

    def __call__(self, **kwargs: Any) -> dict[str, Any]: ...


class ScanPayloadBuilderFn(Protocol):
    """Builds a scan payload dict (no args, returns mapping)."""

    def __call__(self) -> dict[str, Any]: ...


class DIFactoryOverride(Protocol):
    """Overrides a DI factory: receives di + role_path + scan_options, returns the produced object."""

    def __call__(
        self, di: Any, role_path: str, scan_options: dict[str, Any]
    ) -> Any: ...


class BlockerFactBuilder(Protocol):
    """Assembles scan-policy blocker facts from runtime state."""

    def __call__(self, **kwargs: Any) -> Any: ...


class EnsurePreparedPolicyBundleFn(Protocol):
    """Ensures the prepared_policy_bundle is set on scan_options."""

    def __call__(self, *, scan_options: dict[str, Any], di: Any) -> Any: ...
