# Day 42 — Configurable overlap per job

## Purpose

Day 42 makes recovery overlap a persisted per-job setting instead of a hard-coded five-millimetre value. New jobs accept `overlap_mm` during creation and existing jobs receive a migration-safe default of `5.0` millimetres through schema migration 5.

The setting can be updated with:

```text
POST /api/jobs/<job_id>/overlap
```

with a JSON body such as `{ "overlap_mm": 12.5 }`. Updates are recorded as `JOB_OVERLAP_UPDATED` events. Preview and continuation requests use the stored per-job value when they omit an explicit override; explicit request values remain supported for controlled tests and operator workflows.

The dashboard displays and sends the per-job overlap input for both the continuation preview and continuation-generation actions. Preview region metadata preserves exact millimetre boundaries, while image rendering converts the values to pixels for the source image dimensions.

Negative overlap values are rejected with `INVALID_OVERLAP`. This feature remains part of assisted recovery and does not certify physical printer alignment.

## Verification

```bash
python3 test_job_overlap.py
```

The focused test verifies migration persistence, creation-time configuration, update auditing, preview defaults, continuation defaults and invalid-value handling. The complete non-destructive regression suite, Black and Ruff checks also pass.
