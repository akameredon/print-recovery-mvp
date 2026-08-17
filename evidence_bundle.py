from __future__ import annotations

from typing import Any


def build_evidence_bundle(
    *,
    job: dict[str, Any],
    manifest: dict[str, Any],
    recovery_report: dict[str, Any],
    checkpoints: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "bundle_schema": "print-recovery.evidence-handoff/v1",
        "job_id": job.get("id"),
        "created_at": recovery_report.get("generated_at"),
        "handoff_status": "operator_review_required",
        "manifest": manifest,
        "recovery_report": recovery_report,
        "checkpoints": checkpoints,
        "events": events,
        "operator_checklist": [
            {
                "item": "Confirm source integrity",
                "complete": manifest.get("job", {}).get("source_integrity") == "verified",
            },
            {"item": "Review latest durable checkpoint", "complete": bool(checkpoints)},
            {"item": "Review interruption and lifecycle evidence", "complete": bool(events)},
            {"item": "Confirm registration result before continuation", "complete": False},
            {"item": "Record operator approval or rejection", "complete": False},
        ],
        "limitations": [
            "This bundle organizes evidence for assisted recovery.",
            "It does not certify exact physical printer position.",
            "Continuation remains subject to operator confirmation and recovery-safety blockers.",
        ],
    }


def render_handoff_markdown(bundle: dict[str, Any]) -> str:
    checklist = bundle.get("operator_checklist", [])
    lines = [
        f"# Evidence Handoff Bundle — {bundle.get('job_id')}",
        "",
        f"- Handoff status: **{bundle.get('handoff_status')}**",
        f"- Source integrity: **{bundle.get('manifest', {}).get('job', {}).get('source_integrity')}**",
        f"- Checkpoints: **{len(bundle.get('checkpoints', []))}**",
        f"- Events: **{len(bundle.get('events', []))}**",
        "",
        "## Operator checklist",
        "",
    ]
    lines.extend(f"- [{'x' if item['complete'] else ' '}] {item['item']}" for item in checklist)
    lines.extend(
        [
            "",
            "> This bundle is an assisted-recovery handoff, not a physical-position certification.",
            "",
        ]
    )
    return "\n".join(lines)
