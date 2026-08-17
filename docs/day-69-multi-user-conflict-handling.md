# Day 69 — Multi-User Conflict Handling

**Status:** Implemented and verified  
**Roadmap day:** 69  
**Scope:** Prevent stale users from overwriting a newer job mutation

## Delivered

Day 69 adds a durable integer `revision` field to jobs through schema migration 13. The revision starts at zero and increments when the job-overlap mutation succeeds. Clients can send `expected_revision` in the request body or an `If-Match` header. When the supplied revision does not match the current job revision, the API rejects the mutation with `409 JOB_CONFLICT` and returns the current revision, current update timestamp and job ID so the client can reload safely.

The overlap endpoint remains backward-compatible for callers that do not send a revision token, while clients that opt into concurrency protection receive an atomic conditional update. The response includes the new revision after a successful mutation. A zero revision is treated as a valid token, preventing the common falsy-value race bug.

| Scenario | Result |
|---|---|
| First user updates with current revision | Update succeeds and revision increments |
| Second user submits the old revision | `409 JOB_CONFLICT`; no overwrite occurs |
| Second user reloads and retries with current revision | Update succeeds |
| Malformed revision token | `400 INVALID_JOB_REVISION` |
| No revision token | Backward-compatible update behavior |

## Safety and audit boundary

This is an application-level optimistic-concurrency guard. It warns users about stale job state; it does not automatically merge conflicting recovery decisions, prove physical printer position or authorize a print. Operators must reload and review the current evidence before retrying. Existing workspace isolation, role controls and audit/event history remain in force.

## Verification evidence

The focused `test_job_conflicts.py` test passed two authenticated clients reading the same revision, blocked the stale update, returned the current revision metadata, allowed a reload-and-retry, and rejected malformed revision input. Migration and diagnostics tests passed through schema version 13.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, audit-log, workspace, profile, adapter, owner-outcomes, dashboard, observer, trace and usability tests remained passing.
