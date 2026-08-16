# Day 16 — Unified recovery-evidence timeline

## Purpose

Day 16 adds a chronological view of the evidence collected for a recovery decision. Instead of requiring an operator to inspect checkpoints, interruptions, status history, events and decisions separately, the endpoint presents them as one ordered timeline.

## Endpoint

```text
GET /api/jobs/<job_id>/timeline
GET /api/jobs/<job_id>/timeline?limit=100
```

The response includes `total`, the applied `limit`, a `truncated` flag, the ordered `items` array and the request correlation ID. The limit defaults to 100 and must be between 1 and 500. Items are ordered by timestamp, with deterministic kind and record-ID tie breakers.

## Evidence kinds

| Kind | Source | Contents |
|---|---|---|
| `status_transition` | Job status history | Previous status, new status, reason and source. |
| `checkpoint` | Checkpoint records | Position, band, state, evidence and confidence. |
| `event` | Domain events | Event type, source and decoded payload. |
| `decision` | Recovery decisions | Selected position, overlap, mode, recommendation, confidence and operator action. |

The endpoint is read-only. It does not create evidence or alter the job state. Unknown jobs return the standard `JOB_NOT_FOUND` response, while invalid limits return `INVALID_LIMIT`.

## Verification

The focused test creates a job, records a checkpoint and interruption, generates a continuation decision and verifies that all four evidence kinds are present in chronological order. It also checks truncation, correlation-ID propagation, invalid limits and missing-job handling:

```bash
python3 test_timeline.py
```

The timeline is an operator-audit aid. It does not prove physical printer position; physical confirmation remains a separate evidence level in the assisted-recovery workflow.
