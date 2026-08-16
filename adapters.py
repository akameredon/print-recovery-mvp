from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

SIMULATED_EVENT_TYPES = {
    "JOB_STARTED",
    "PROGRESS",
    "INTERRUPTED",
    "JOB_COMPLETED",
}


@dataclass(frozen=True)
class AdapterEvent:
    event_type: str
    source: str
    payload: dict[str, Any]
    emitted_at: str


class SimulatedAdapter:
    """Deterministic adapter stand-in used before vendor integration exists."""

    name = "simulated_adapter"

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> AdapterEvent:
        normalized = str(event_type).strip().upper()
        if normalized not in SIMULATED_EVENT_TYPES:
            allowed = ", ".join(sorted(SIMULATED_EVENT_TYPES))
            raise ValueError(f"event_type must be one of: {allowed}")
        return AdapterEvent(
            event_type=normalized,
            source=self.name,
            payload=dict(payload or {}),
            emitted_at=datetime.now(timezone.utc).isoformat(),
        )
