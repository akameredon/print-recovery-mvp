from __future__ import annotations

from html import escape
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


def render_printable_recovery_report(report: dict[str, Any]) -> str:
    selected = report.get("selected_coordinate") or {}
    confidence = report.get("confidence") or {}
    safety = report.get("recovery_safety") or {}
    blockers = (
        ", ".join(item.get("code", "unknown") for item in safety.get("blockers", [])) or "none"
    )
    warnings = (
        ", ".join(item.get("code", "unknown") for item in safety.get("warnings", [])) or "none"
    )
    rows = [
        ("Job ID", report.get("job_id")),
        ("File", report.get("file_name")),
        ("Generated", report.get("generated_at")),
        ("Readiness", report.get("readiness")),
        ("Selected coordinate", f"{selected.get('y_mm', 'not selected')} mm"),
        (
            "Confidence",
            f"{confidence.get('level', 'not available')} ({confidence.get('score', 'n/a')})",
        ),
        ("Source integrity", (report.get("source_integrity") or {}).get("status")),
        ("Safe to generate", safety.get("safe_to_generate", False)),
        ("Blockers", blockers),
        ("Warnings", warnings),
        ("Checkpoint", f"{(report.get('checkpoint') or {}).get('y_mm', 'none')} mm"),
        ("Interruption", (report.get("interruption") or {}).get("event_type", "none")),
        ("Operator review", (report.get("operator_review") or {}).get("action", "pending")),
    ]
    table = "".join(
        f"<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>"
        for label, value in rows
    )
    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Recovery Report — {escape(str(report.get('job_id')))}</title>
<style>body{{font-family:Arial,sans-serif;color:#18212b;max-width:850px;margin:32px auto;padding:0 24px}}h1{{border-bottom:2px solid #18212b;padding-bottom:10px}}table{{border-collapse:collapse;width:100%;margin:22px 0}}th,td{{border:1px solid #c7d0d9;padding:10px;text-align:left}}th{{width:32%;background:#f1f5f8}}.notice{{border-left:4px solid #b07a00;background:#fff8e8;padding:12px}}@media print{{body{{margin:0;max-width:none}}.no-print{{display:none}}}}</style></head>
<body><button class=\"no-print\" onclick=\"window.print()\">Print or save as PDF</button>
<h1>Recovery Report</h1><table>{table}</table>
<div class=\"notice\"><strong>Safety boundary:</strong> This report organizes recorded software evidence. It does not certify exact physical printer position, print quality or safe continuation without operator review.</div>
</body></html>"""
