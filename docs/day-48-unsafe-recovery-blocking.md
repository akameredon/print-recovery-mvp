# Day 48 — Unsafe-recovery blocking rules

## Purpose

Day 48 adds explicit safety rules that block continuation generation when the evidence required for an assisted recovery is missing or mismatched. The rules cover three unsafe conditions:

| Condition | Blocker code | Behavior |
|---|---|---|
| Source file is missing | `SOURCE_MISSING` | Continuation generation returns HTTP 409 and remains blocked |
| Source hash differs from the job manifest | `SOURCE_CHANGED` | Continuation generation returns HTTP 409 and remains blocked |
| No durable checkpoint exists | `CHECKPOINT_MISSING` | Continuation generation returns HTTP 409 and remains blocked |

Recovery readiness now includes a structured `recovery_safety` object with `safe_to_generate`, `status`, `blockers` and `warnings`. A verified source and checkpoint are necessary before generating a continuation. Missing interruption history remains a review warning rather than a substitute for evidence.

This feature enforces the project’s assisted-recovery rule: the software refuses to infer a safe continuation position when the source or checkpoint evidence is unavailable. It does not delete data or attempt automatic repair; the operator must restore or review the underlying evidence first.

## Verification

```bash
python3 test_recovery_safety.py
```

The focused test covers pure safety rules, missing-checkpoint blocking, changed-source blocking and structured blocker responses. Existing successful continuation fixtures were updated to provide durable checkpoints. The complete non-destructive regression suite, Black and Ruff checks pass.
