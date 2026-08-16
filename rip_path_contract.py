from __future__ import annotations

import re
from typing import Any

PLACEHOLDERS = {"", "TO_BE_CONFIRMED", "UNKNOWN", "N/A"}
ALLOWED_MODES = {"hot_folder", "watched_folder", "manual_export", "api"}
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")


def _is_placeholder(value: str) -> bool:
    return value.strip().upper() in PLACEHOLDERS


def _contains_traversal(value: str) -> bool:
    return any(part == ".." for part in value.replace("\\", "/").split("/"))


def validate_path_contract(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    mode = str(contract.get("connection_mode", "")).strip().lower()
    input_path = str(contract.get("job_input_path", "")).strip()
    output_path = str(contract.get("job_output_or_hotfolder", "")).strip()
    if mode not in ALLOWED_MODES:
        errors.append({"code": "INVALID_CONNECTION_MODE", "field": "connection_mode"})
    for field, value in (("job_input_path", input_path), ("job_output_or_hotfolder", output_path)):
        if _is_placeholder(value):
            errors.append({"code": "PATH_UNCONFIRMED", "field": field})
        elif _contains_traversal(value):
            errors.append({"code": "PATH_TRAVERSAL", "field": field})
        elif not (_WINDOWS_DRIVE.match(value) or value.startswith(("/", "\\\\"))):
            warnings.append({"code": "PATH_NOT_ABSOLUTE", "field": field})
    if input_path and output_path and input_path.casefold() == output_path.casefold():
        errors.append({"code": "PATH_COLLISION", "field": "job_input_path"})
    if mode in {"hot_folder", "watched_folder"} and not output_path:
        errors.append({"code": "WATCHED_PATH_REQUIRED", "field": "job_output_or_hotfolder"})
    status = "invalid" if errors else ("warning" if warnings else "ready_for_signoff")
    return {"status": status, "errors": errors, "warnings": warnings}
