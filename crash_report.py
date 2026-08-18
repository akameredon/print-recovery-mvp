from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SENSITIVE_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "authorization",
    "cookie",
)
PATH_KEY_PARTS = ("path", "source", "output", "log")


def redact_value(value: Any, key: str = "") -> Any:
    lowered = key.lower()
    if any(part in lowered for part in SENSITIVE_KEY_PARTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(item_key): redact_value(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item, key) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~-]+", r"\1[REDACTED]", value)
        if any(part in lowered for part in PATH_KEY_PARTS):
            return Path(value).name or "[REDACTED]"
    return value


def read_recent_log_records(log_path: Path, limit: int = 100) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    records = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            records.append({"message": "unstructured log line omitted"})
            continue
        records.append(redact_value(payload))
    return records


def build_crash_report(
    *,
    report_id: str,
    generated_at: str,
    app_version: str,
    log_path: Path,
    diagnostics: dict[str, Any],
    configuration: dict[str, Any],
) -> dict[str, Any]:
    records = read_recent_log_records(log_path)
    errors = [record for record in records if record.get("severity") in {"ERROR", "CRITICAL"}]
    safe_configuration = {
        "log_level": configuration.get("log_level"),
        "max_upload_mb": configuration.get("max_upload_mb"),
        "upload_rate_limit_per_minute": configuration.get("upload_rate_limit_per_minute"),
    }
    return {
        "report_type": "structured_crash_report",
        "report_id": report_id,
        "generated_at": generated_at,
        "service": "print-recovery-mvp",
        "version": app_version,
        "diagnostics": {
            "status": diagnostics.get("status"),
            "checks": {
                key: value
                for key, value in diagnostics.get("checks", {}).items()
                if key in {"database", "clock"}
            },
        },
        "configuration": safe_configuration,
        "recent_errors": errors[-20:],
        "recent_log_count": len(records),
        "redaction": {
            "secrets_removed": True,
            "paths_reduced_to_basenames": True,
            "raw_log_export": False,
        },
        "limitations": "This report contains host-side diagnostics and does not establish physical printer state or continuation safety.",
    }
