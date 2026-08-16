from __future__ import annotations

from typing import Any

EVIDENCE_SCORES = {
    "prepared": 0.25,
    "transmitted": 0.50,
    "acknowledged": 0.75,
    "physical": 0.95,
}


def calculate_checkpoint_confidence(checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Return a transparent score; this is assisted-recovery evidence, not certification."""
    evidence = str(checkpoint.get("evidence", "transmitted")).lower()
    score = EVIDENCE_SCORES.get(evidence, EVIDENCE_SCORES["transmitted"])
    factors = [f"evidence:{evidence if evidence in EVIDENCE_SCORES else 'transmitted'}"]

    if checkpoint.get("logical_band") is not None and checkpoint.get("pass_number") is not None:
        score += 0.05
        factors.append("logical_band_and_pass_present:+0.05")
    else:
        factors.append("logical_band_or_pass_missing:+0.00")

    try:
        y_mm = float(checkpoint.get("y_mm"))
    except (TypeError, ValueError):
        y_mm = -1
    if y_mm >= 0:
        factors.append("non_negative_coordinate:+0.00")
    else:
        score -= 0.25
        factors.append("invalid_coordinate:-0.25")

    score = round(max(0.0, min(score, 1.0)), 2)
    if score >= 0.85:
        level = "high"
    elif score >= 0.60:
        level = "medium"
    else:
        level = "low"
    return {"score": score, "level": level, "factors": factors}
