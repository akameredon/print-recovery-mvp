# Day 15 — Recovery-readiness assessment

## Purpose

Day 15 adds a single operator-facing assessment endpoint that combines the evidence needed before preparing a continuation print. It checks the source-file SHA-256 integrity, the latest recorded checkpoint and the presence of an interruption transition.

## Endpoint

```text
GET /api/jobs/<job_id>/readiness
```

The endpoint is deliberately advisory. It does not change the job status, generate a continuation file or authorize a print automatically. `operator_confirmation_required` is always `true` because the current MVP uses assisted recovery.

## Readiness states

| State | Conditions | Meaning |
|---|---|---|
| `blocked` | Source is missing or changed, or no checkpoint exists | Recovery evidence is insufficient or unsafe to proceed. |
| `review_required` | Source is verified and a checkpoint exists, but no interruption transition is recorded | The operator must confirm why recovery is being considered. |
| `ready_for_operator_review` | Source is verified, a checkpoint exists and an interruption transition is recorded | The evidence set is complete enough for operator review and continuation preparation. |

The response includes the expected and actual source hashes, checkpoint record, interruption record, current job status, reason and request correlation ID. A missing job returns the standard `JOB_NOT_FOUND` error.

## Verification

The focused test creates jobs for all three states, modifies a source file to verify integrity blocking, checks the correlation ID and confirms missing-job handling:

```bash
python3 test_readiness.py
```

This is a readiness assessment, not a certified printer/RIP integration. The result must not be interpreted as proof that the printer physically stopped at the recorded coordinate.
