from __future__ import annotations

from typing import Any

SIGNAL_DEFINITIONS = {
    "host_job_created": {
        "family": "host",
        "evidence": "prepared",
        "recovery_effect": "Identifies the source job but not transmitted or printed output.",
    },
    "host_transmission_started": {
        "family": "host",
        "evidence": "transmitted",
        "recovery_effect": "Shows host transmission began; printer buffering remains unknown.",
    },
    "host_transmission_completed": {
        "family": "host",
        "evidence": "transmitted",
        "recovery_effect": "Shows host handoff completed; physical completion remains unknown.",
    },
    "rip_queue_seen": {
        "family": "rip",
        "evidence": "acknowledged",
        "recovery_effect": "Shows the RIP observed the job; printer position remains unknown.",
    },
    "rip_progress_percent": {
        "family": "rip",
        "evidence": "acknowledged",
        "recovery_effect": "Provides RIP progress; buffering and physical seam still require review.",
    },
    "printer_status_feedback": {
        "family": "printer",
        "evidence": "acknowledged",
        "recovery_effect": "Provides device feedback; exact media coordinate requires validation.",
    },
    "physical_checkpoint": {
        "family": "physical",
        "evidence": "physical",
        "recovery_effect": "Strongest available evidence, but still requires controlled target validation.",
    },
}


def assess_signal_matrix(observed_signals: list[str]) -> dict[str, Any]:
    normalized = {str(signal).strip().lower() for signal in observed_signals}
    rows = []
    for signal, definition in SIGNAL_DEFINITIONS.items():
        rows.append({"signal": signal, "available": signal in normalized, **definition})
    available = [row for row in rows if row["available"]]
    families = sorted({row["family"] for row in available})
    if any(
        SIGNAL_DEFINITIONS[signal]["family"] == "physical"
        for signal in normalized
        if signal in SIGNAL_DEFINITIONS
    ):
        recovery_mode = "assisted_review_required"
        confidence_limit = (
            "physical evidence is recorded but target-specific validation is still required"
        )
    elif "printer_status_feedback" in normalized or "rip_progress_percent" in normalized:
        recovery_mode = "assisted_test_first"
        confidence_limit = "host/RIP/device progress does not prove physical seam position"
    else:
        recovery_mode = "assisted_restart_or_registration_check"
        confidence_limit = "host-side signals alone do not prove printer or media position"
    return {
        "status": "assessed",
        "observed_signals": sorted(normalized),
        "available_families": families,
        "rows": rows,
        "recovery_mode": recovery_mode,
        "confidence_limit": confidence_limit,
    }
