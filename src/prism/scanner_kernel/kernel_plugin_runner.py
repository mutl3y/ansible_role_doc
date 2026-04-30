"""Kernel plugin lifecycle runner for phase-based execution."""

from __future__ import annotations

import logging
from typing import Any, Callable, cast

from prism.scanner_core.protocols_runtime import KernelLifecyclePlugin, PluginLoader

logger = logging.getLogger(__name__)


def run_kernel_plugin_orchestrator(
    *,
    platform: str,
    target_path: str,
    scan_options: dict[str, Any],
    load_plugin_fn: PluginLoader,
    scan_id: str = "kernel-scan",
    fail_fast: bool = True,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute baseline lifecycle phases on a loaded kernel plugin.

    Phase Execution Contract:
    -------------------------
    Plugin lifecycle phases are ORDERED and STATEFUL:
    - prepare → scan → analyze → finalize
    - Each phase depends on successful completion of upstream phases
    - Failed phase blocks downstream execution to prevent corrupt state

    Phase State Transitions:
    ------------------------
    - "completed": Phase executed successfully
    - "skipped": Handler not implemented (hasattr check)
    - "failed": Handler raised exception
    - "skipped_due_to_upstream_failure": Downstream phase not executed because
      an upstream phase failed (respects phase dependencies)

    Fail-Fast Semantics:
    -------------------
    - fail_fast=True: Break immediately on first phase failure (strict mode)
    - fail_fast=False: Skip downstream phases for this plugin, mark errors as
      recoverable; allows multi-plugin orchestration to continue (fail-per-plugin)

    Args:
        platform: Platform identifier (e.g., "ansible")
        target_path: Path to scan target
        scan_options: Scan configuration options
        load_plugin_fn: Function to load plugin by platform
        scan_id: Unique scan identifier
        fail_fast: If True, break on first failure; if False, skip downstream
        context: Optional execution context

    Returns:
        Response dict with phase_results, metadata, errors, and payload
    """
    logger.info(
        "Kernel orchestrator started: scan_id=%s platform=%s target=%s fail_fast=%s",
        scan_id,
        platform,
        target_path,
        fail_fast,
    )

    import copy

    request: dict[str, Any] = {
        "scan_id": scan_id,
        "platform": platform,
        "target_path": target_path,
        "options": copy.copy(scan_options),
    }
    if isinstance(context, dict):
        request["context"] = copy.copy(context)

    response: dict[str, Any] = {
        "scan_id": scan_id,
        "platform": platform,
        "phase_results": {},
        "metadata": {"kernel_orchestrator": "fsrc-v1"},
    }

    plugin: KernelLifecyclePlugin = cast(
        KernelLifecyclePlugin, load_plugin_fn(platform)
    )
    phase_handlers: list[tuple[str, Callable[..., dict[str, Any] | None] | None]] = [
        ("prepare", plugin.prepare if hasattr(plugin, "prepare") else None),
        ("scan", plugin.scan if hasattr(plugin, "scan") else None),
        ("analyze", plugin.analyze if hasattr(plugin, "analyze") else None),
        ("finalize", plugin.finalize if hasattr(plugin, "finalize") else None),
    ]

    upstream_phase_failed = False

    for phase, handler in phase_handlers:
        if handler is None:
            logger.debug("Phase %s: skipped (handler not implemented)", phase)
            response["phase_results"][phase] = {"phase": phase, "status": "skipped"}
            continue

        if upstream_phase_failed:
            logger.warning(
                "Phase %s: skipped due to upstream failure in previous phase",
                phase,
            )
            response["phase_results"][phase] = {
                "phase": phase,
                "status": "skipped_due_to_upstream_failure",
                "reason": "Upstream phase failed; phase dependencies require successful prior execution",
            }
            continue

        logger.info("Phase %s: executing", phase)
        try:
            if phase in {"prepare", "scan"}:
                phase_output = handler(request)
            else:
                phase_output = handler(request, response)
        except Exception as exc:
            logger.error("Phase %s: FAILED with exception: %s", phase, exc)
            error_envelope = {
                "code": "KERNEL_PLUGIN_PHASE_FAILED",
                "message": str(exc),
                "phase": phase,
                "recoverable": not fail_fast,
            }
            response.setdefault("errors", []).append(error_envelope)
            response["phase_results"][phase] = {
                "phase": phase,
                "status": "failed",
                "error": error_envelope,
            }

            upstream_phase_failed = True

            if fail_fast:
                logger.error(
                    "Phase %s: fail_fast=True, breaking plugin execution", phase
                )
                break

            logger.warning(
                "Phase %s: fail_fast=False, marking downstream phases as skipped",
                phase,
            )
            continue

        logger.info("Phase %s: completed successfully", phase)
        _merge_phase_output(response=response, phase=phase, phase_output=phase_output)
        response["phase_results"][phase] = {"phase": phase, "status": "completed"}

    logger.info(
        "Kernel orchestrator finished: scan_id=%s phases_completed=%d",
        scan_id,
        sum(
            1
            for result in response["phase_results"].values()
            if result.get("status") == "completed"
        ),
    )

    return response


def _merge_phase_output(
    *,
    response: dict[str, Any],
    phase: str,
    phase_output: Any,
) -> None:
    if not isinstance(phase_output, dict):
        return

    if phase == "scan" and "payload" not in phase_output:
        response["payload"] = dict(phase_output)

    payload = phase_output.get("payload")
    if isinstance(payload, dict):
        response["payload"] = dict(payload)

    metadata = phase_output.get("metadata")
    if isinstance(metadata, dict):
        response.setdefault("metadata", {}).update(metadata)

    for key in ("warnings", "errors", "provenance"):
        value = phase_output.get(key)
        if isinstance(value, list):
            response.setdefault(key, []).extend(value)
