"""Kernel plugin lifecycle runner for phase-based execution."""

from __future__ import annotations

from typing import Any, Callable


def run_kernel_plugin_orchestrator(
    *,
    platform: str,
    target_path: str,
    scan_options: dict[str, Any],
    load_plugin_fn: Callable[[str], Any],
    scan_id: str = "kernel-scan",
    fail_fast: bool = True,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute baseline lifecycle phases on a loaded kernel plugin."""
    request: dict[str, Any] = {
        "scan_id": scan_id,
        "platform": platform,
        "target_path": target_path,
        "options": dict(scan_options),
    }
    if isinstance(context, dict):
        request["context"] = dict(context)

    response: dict[str, Any] = {
        "scan_id": scan_id,
        "platform": platform,
        "phase_results": {},
        "metadata": {"kernel_orchestrator": "fsrc-v1"},
    }

    plugin = load_plugin_fn(platform)
    phases = ("prepare", "scan", "analyze", "finalize")

    for phase in phases:
        handler = getattr(plugin, phase, None)
        if not callable(handler):
            response["phase_results"][phase] = {"phase": phase, "status": "skipped"}
            continue

        try:
            if phase in {"prepare", "scan"}:
                phase_output = handler(request)
            else:
                phase_output = handler(request, response)
        except Exception as exc:
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
            if fail_fast:
                break
            continue

        _merge_phase_output(response=response, phase=phase, phase_output=phase_output)
        response["phase_results"][phase] = {"phase": phase, "status": "completed"}

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
