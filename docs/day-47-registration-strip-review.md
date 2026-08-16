# Day 47 — Operator confirmation of registration-strip results

## Purpose

Day 47 adds an explicit operator review step after a registration strip is generated. The operator can record one of three results: `aligned`, `misaligned` or `uncertain`, together with an optional note. The review is stored as a `REGISTRATION_STRIP_REVIEWED` event linked to the generated strip filename.

The review endpoint is:

```text
POST /api/jobs/<job_id>/registration-strip/review
```

The latest review and complete review history are available through:

```text
GET /api/jobs/<job_id>/registration-strip/review
```

A review cannot be recorded until a registration strip has been generated. If no filename is supplied, the API resolves the latest generated strip for that job. A supplied filename must belong to a generated strip event for the same job. The response and summary make the pending or completed operator-confirmation state explicit.

The dashboard provides controls to confirm alignment, mark the strip misaligned or mark the result uncertain. This review does not automatically authorize continuation or change the existing assisted-recovery safeguards.

## Verification

```bash
python3 test_registration_strip_review.py
```

The focused test verifies pending state, no-strip protection, aligned confirmation, latest-review retrieval, audit-event persistence and invalid-result handling. The complete non-destructive regression suite, Black and Ruff checks pass.
