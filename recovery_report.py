from __future__ import annotations

from typing import Any


def render_recovery_report(report: dict[str, Any]) -> str:
    selected = report.get("selected_coordinate") or {}
    confidence = report.get("confidence") or {}
    safety = report.get("recovery_safety") or {}
    lines = [
        f"# Recovery Report — {report['job_id']}",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Recovery summary",
        "",
        f"- Readiness: **{report['readiness']}**",
        f"- Selected coordinate: **{selected.get('y_mm', 'not selected')} mm**",
        f"- Confidence: **{confidence.get('level', 'not available')}** ({confidence.get('score', 'n/a')})",
        f"- Source integrity: **{report['source_integrity']['status']}**",
        "",
        "## Safety",
        "",
        f"- Safe to generate: **{safety.get('safe_to_generate', False)}**",
        f"- Blockers: {', '.join(item['code'] for item in safety.get('blockers', [])) or 'none'}",
        f"- Warnings: {', '.join(item['code'] for item in safety.get('warnings', [])) or 'none'}",
        "",
        "## Evidence",
        "",
        f"- Checkpoint: `{report['checkpoint'].get('y_mm', 'none') if report.get('checkpoint') else 'none'} mm`",
        f"- Interruption: `{report['interruption'].get('event_type', 'none') if report.get('interruption') else 'none'}`",
        f"- Operator review: `{report['operator_review'].get('action', 'pending') if report.get('operator_review') else 'pending'}`",
        "",
        "> This report organizes recorded evidence for assisted recovery. It does not certify exact physical printer position.",
        "",
    ]
    return "\n".join(lines)
