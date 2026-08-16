from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = (
    "manufacturer",
    "printer_model",
    "rip_name",
    "rip_version",
    "connection_mode",
    "job_input_path",
    "job_output_or_hotfolder",
)
PLACEHOLDER_VALUES = {"", "TO_BE_CONFIRMED", "UNKNOWN", "N/A"}


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for field in REQUIRED_FIELDS:
        value = str(contract.get(field, "")).strip()
        if value in PLACEHOLDER_VALUES:
            errors.append({"code": "CONTRACT_FIELD_UNCONFIRMED", "field": field})
    if contract.get("recovery_mode") != "assisted_only":
        errors.append({"code": "UNSAFE_RECOVERY_MODE", "field": "recovery_mode"})
    if not contract.get("observable_signals"):
        warnings.append({"code": "NO_OBSERVABLE_SIGNALS", "field": "observable_signals"})
    if not contract.get("physical_validation_required"):
        warnings.append(
            {"code": "NO_PHYSICAL_VALIDATION_GATE", "field": "physical_validation_required"}
        )
    status = "invalid" if errors else ("warning" if warnings else "ready_for_signoff")
    if contract.get("status") != "signed_off":
        warnings.append({"code": "SIGNOFF_REQUIRED", "field": "status"})
        if status == "ready_for_signoff":
            status = "warning"
    return {"status": status, "errors": errors, "warnings": warnings}
