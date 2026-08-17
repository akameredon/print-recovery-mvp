from __future__ import annotations

from typing import Any


def summarize_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    safety = readiness.get("recovery_safety") or {}
    blockers = list(safety.get("blockers") or [])
    warnings = list(safety.get("warnings") or [])
    actions: list[str] = []
    if blockers:
        actions.append("Resolve every recovery blocker before generating a continuation.")
    if readiness.get("source_integrity", {}).get("status") != "verified":
        actions.append("Verify the source file and hash against the protected job manifest.")
    if not readiness.get("checkpoint_confidence"):
        actions.append("Record a durable checkpoint before evaluating continuation.")
    if readiness.get("interruption") is None:
        actions.append("Record the interruption reason and operator note.")
    if not blockers and warnings:
        actions.append("Review warnings and perform a registration test before continuation.")
    if not actions:
        actions.append("Review the evidence bundle, then record explicit operator approval or rejection.")
    return {
        "job_id": readiness.get("job_id"),
        "readiness": readiness.get("readiness"),
        "headline": {
            "blocked": "Recovery blocked" if blockers else None,
            "review": "Operator review required" if not blockers else None,
            "ready": "Evidence is ready for operator review" if not blockers and not warnings else None,
        },
        "blockers": blockers,
        "warnings": warnings,
        "next_actions": actions,
        "operator_confirmation_required": True,
        "safe_to_generate": bool(safety.get("safe_to_generate")) and not blockers,
    }
