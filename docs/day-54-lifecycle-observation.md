# Day 54 — RIP queue and hot-folder lifecycle observation

## Purpose

Day 54 adds a lifecycle observer for queue and hot-folder-compatible events without controlling a printer or assuming vendor-specific signals. The API is:

```text
POST /api/jobs/<job_id>/lifecycle/observe
```

It accepts an ordered event sequence containing `JOB_DISCOVERED`, `JOB_QUEUED`, `JOB_STARTED`, `PROGRESS`, `INTERRUPTED` or `JOB_COMPLETED`. The observer returns the final state, every state transition, preserved payloads and validation errors. Valid observations are persisted as `RIP_LIFECYCLE_OBSERVED` events with the declared source and raw event sequence.

| Observation | Result |
|---|---|
| Queue, start, progress and completion sequence | Observed with final `completed` state |
| Interruption before completion | Observed with final `interrupted` state |
| Unknown event type | Rejected with `UNKNOWN_LIFECYCLE_EVENT` |
| Event after an interrupted or completed state | Rejected with `EVENT_AFTER_TERMINAL_STATE` |

The feature is suitable for synthetic adapter events now and for a future real RIP observer once the target shop confirms which queue, hot-folder or host signals are available. It does not claim printer control or physical completion.

## Verification

```bash
python3 test_lifecycle_observer.py
```

The focused test verifies ordered transitions, progress payload preservation, terminal-state protection, invalid-event handling, API output and raw event persistence. The complete non-destructive regression suite, Black and Ruff checks pass.
