# Day 17 — Operator review recording

## Purpose

Day 17 adds an explicit review step after a continuation decision has been generated. The operator can record whether the proposed recovery is approved or rejected, together with a short note. This makes the human confirmation visible in the audit trail instead of leaving it implicit.

## Endpoint

```text
POST /api/jobs/<job_id>/review
```

The request accepts JSON or form data:

```json
{
  "action": "approved",
  "note": "Registration strip checked"
}
```

The action must be `approved` or `rejected`; notes are limited to 1,000 characters. A job must exist and must already have a persisted recovery decision. Otherwise the endpoint returns `JOB_NOT_FOUND` or `NO_DECISION`.

The latest decision’s `operator_action` is updated, and an append-only `RECOVERY_REVIEWED` event is recorded with the action, note and decision ID. The endpoint does not change the job status and does not authorize a printer automatically. `operator_confirmation_required` remains true because this is assisted recovery.

## Safety behavior

Approval records the operator’s confirmation but is not a claim that the printer is physically aligned. Rejection records that the proposed recovery should not proceed. The review operation is therefore an audit action, not an automated print command.

## Verification

The focused test covers approved and rejected reviews, latest-decision persistence, audit-event creation, correlation-ID propagation, invalid actions, overlong notes and missing jobs:

```bash
python3 test_review.py
```
