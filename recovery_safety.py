from __future__ import annotations

from typing import Any


def assess_recovery_safety(
    *,
    source_integrity: str,
    has_checkpoint: bool,
    has_interruption: bool,
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    if source_integrity == "missing":
        blockers.append(
            {"code": "SOURCE_MISSING", "message": "The recorded source file is missing."}
        )
    elif source_integrity == "changed":
        blockers.append(
            {
                "code": "SOURCE_CHANGED",
                "message": "The source hash does not match the recorded job manifest.",
            }
        )
    elif source_integrity != "verified":
        blockers.append(
            {"code": "SOURCE_UNVERIFIED", "message": "Source integrity is not verified."}
        )
    if not has_checkpoint:
        blockers.append(
            {
                "code": "CHECKPOINT_MISSING",
                "message": "No durable checkpoint identifies a recovery position.",
            }
        )
    warnings: list[dict[str, str]] = []
    if not has_interruption:
        warnings.append(
            {
                "code": "INTERRUPTION_MISSING",
                "message": "No interruption event has been recorded yet.",
            }
        )
    return {
        "safe_to_generate": not blockers,
        "status": "blocked" if blockers else ("review_required" if warnings else "ready"),
        "blockers": blockers,
        "warnings": warnings,
    }
