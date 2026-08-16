from __future__ import annotations

from typing import Any

EVENT_TO_STATE = {
    "JOB_DISCOVERED": "discovered",
    "JOB_QUEUED": "queued",
    "JOB_STARTED": "started",
    "PROGRESS": "started",
    "INTERRUPTED": "interrupted",
    "JOB_COMPLETED": "completed",
}
ALLOWED_EVENT_TYPES = set(EVENT_TO_STATE)
TERMINAL_STATES = {"interrupted", "completed"}


def observe_lifecycle(events: list[dict[str, Any]]) -> dict[str, Any]:
    state = "unknown"
    transitions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        event_type = str(event.get("event_type", "")).strip().upper()
        if event_type not in ALLOWED_EVENT_TYPES:
            errors.append(
                {"index": index, "code": "UNKNOWN_LIFECYCLE_EVENT", "event_type": event_type}
            )
            continue
        next_state = EVENT_TO_STATE[event_type]
        if state in TERMINAL_STATES:
            errors.append(
                {
                    "index": index,
                    "code": "EVENT_AFTER_TERMINAL_STATE",
                    "event_type": event_type,
                    "state": state,
                }
            )
            continue
        previous_state = state
        state = next_state
        transition = {
            "index": index,
            "event_type": event_type,
            "from_state": previous_state,
            "to_state": state,
            "payload": dict(event.get("payload") or {}),
            "observed_at": event.get("observed_at"),
        }
        transitions.append(transition)
    return {
        "status": "invalid" if errors else "observed",
        "final_state": state,
        "transitions": transitions,
        "errors": errors,
        "event_count": len(transitions),
    }
