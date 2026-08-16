from __future__ import annotations

from typing import Any

CLASSIFICATION_MATRIX = {
    "POWER_LOSS": {
        "classification": "outage",
        "required_evidence": ["power-loss reason", "last durable checkpoint"],
        "recovery_effect": "Review checkpoint and power-restoration state before assisted recovery.",
    },
    "PROTECTION_TRIP": {
        "classification": "outage",
        "required_evidence": ["protection-trip reason", "last durable checkpoint"],
        "recovery_effect": "Treat as an electrical interruption; operator must confirm safe restart.",
    },
    "PRINTER_ERROR": {
        "classification": "crash",
        "required_evidence": ["printer error reason", "device or RIP diagnostic note"],
        "recovery_effect": "Do not assume physical completion from host progress alone.",
    },
    "OPERATOR_ABORT": {
        "classification": "abort",
        "required_evidence": ["operator-abort reason", "operator note"],
        "recovery_effect": "Require operator review of the intentional stop before continuing.",
    },
    "COMMUNICATION_LOSS": {
        "classification": "communication_loss",
        "required_evidence": ["communication-loss reason", "last host transmission"],
        "recovery_effect": "Use assisted recovery and require a registration check.",
    },
    "MATERIAL_ISSUE": {
        "classification": "material_issue",
        "required_evidence": ["material-issue reason", "operator note"],
        "recovery_effect": "Resolve media condition before any continuation attempt.",
    },
    "UNKNOWN": {
        "classification": "unknown",
        "required_evidence": ["interruption reason", "operator review"],
        "recovery_effect": "Do not infer a safe continuation position.",
    },
}


def classify_interruption(reason: str, note: str = "", source: str = "operator") -> dict[str, Any]:
    normalized = str(reason).strip().upper()
    rule = CLASSIFICATION_MATRIX.get(normalized, CLASSIFICATION_MATRIX["UNKNOWN"])
    evidence = list(rule["required_evidence"])
    if note.strip():
        evidence.append("operator note present")
    return {
        "reason": normalized if normalized in CLASSIFICATION_MATRIX else "UNKNOWN",
        "classification": rule["classification"],
        "source": str(source).strip() or "operator",
        "evidence_requirements": evidence,
        "recovery_effect": rule["recovery_effect"],
        "confidence": (
            "low" if normalized in {"UNKNOWN", "COMMUNICATION_LOSS"} else "review_required"
        ),
    }
