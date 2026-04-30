"""Runtime Protocol contracts for DI factories and orchestrator boundary surfaces.

Replaces weak `Callable[..., Any]` aliases at the scanner_core ↔ scanner_kernel
boundary. Each Protocol documents the contract that previously had to be inferred
from call sites.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from prism.scanner_core.di import DIContainer

from prism.scanner_data.contracts_request import ScanMetadata, ScanOptionsDict
from prism.scanner_data.contracts_request import ScanPolicyBlockerFacts


class PluginLoader(Protocol):
    """Loads a plugin instance by platform name (kernel-side seam)."""

    def __call__(self, platform: str) -> Any: ...


class KernelOrchestrator(Protocol):
    """Invokes the kernel orchestration entrypoint with keyword args."""

    def __call__(
        self,
        *,
        role_path: str,
        scan_options: dict[str, Any],
        route_preflight_runtime: Any,
    ) -> dict[str, Any]: ...


class ScanPayloadBuilderFn(Protocol):
    """Builds a scan payload dict (no args, returns mapping)."""

    def __call__(self) -> dict[str, Any]: ...


class DIFactoryOverride(Protocol):
    """Overrides a DI factory: receives di + role_path + scan_options, returns the produced object."""

    def __call__(
        self, di: "DIContainer", role_path: str, scan_options: dict[str, Any]
    ) -> Any: ...


class BlockerFactBuilder(Protocol):
    """Assembles scan-policy blocker facts from runtime state."""

    def __call__(
        self,
        *,
        scan_options: ScanOptionsDict,
        metadata: ScanMetadata,
        di: "DIContainer",
    ) -> ScanPolicyBlockerFacts: ...


class EnsurePreparedPolicyBundleFn(Protocol):
    """Ensures the prepared_policy_bundle is set on scan_options."""

    def __call__(self, *, scan_options: dict[str, Any], di: "DIContainer") -> None: ...


class KernelLifecyclePlugin(Protocol):
    """Phase-based lifecycle contract for kernel plugins.

    prepare/scan receive only the request; analyze/finalize also receive
    the accumulated response so they can read prior phase outputs.
    """

    def prepare(self, request: dict[str, Any]) -> dict[str, Any] | None: ...

    def scan(self, request: dict[str, Any]) -> dict[str, Any] | None: ...

    def analyze(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any] | None: ...

    def finalize(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any] | None: ...
