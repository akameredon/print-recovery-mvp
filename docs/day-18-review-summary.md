# Day 18 — Recovery-review summary

## Purpose

Day 18 adds a read-only endpoint for inspecting the current review state of a recovery decision. It gives operators and future user interfaces a stable way to distinguish a decision that has not yet been reviewed from one that was approved or rejected.

## Endpoint

```text
GET /api/jobs/<job_id>/review
```

The response includes the latest persisted decision, the current job status, the review state, all `RECOVERY_REVIEWED` audit events and the request correlation ID. The endpoint does not create events or change job state.

## Review states

| State | Meaning |
|---|---|
| `pending` | A recovery decision exists, but no operator review has been recorded. |
| `approved` | The latest decision was explicitly approved by an operator. |
| `rejected` | The latest decision was explicitly rejected by an operator. |

`operator_confirmation_required` is true only while the state is `pending`. A job without a persisted recovery decision returns `NO_DECISION`, while an unknown job returns `JOB_NOT_FOUND`.

## Verification

The focused test creates a persisted continuation decision, verifies the pending state, records approval and rejection, checks the audit-event history and confirms missing-decision and missing-job behavior:

```bash
python3 test_review_summary.py
```

This endpoint is a read-only inspection surface. It does not mean that approval automatically starts a printer or proves physical alignment.
