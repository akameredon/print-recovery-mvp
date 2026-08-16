# Day 37 — Simulated adapter interface

## Purpose

Day 37 adds a deterministic adapter stand-in before vendor-specific Mimaki, Roland or RIP integrations are attempted. The `SimulatedAdapter` validates a small event vocabulary and produces an event envelope with source and UTC emission time.

The API endpoint is:

```text
POST /api/jobs/<job_id>/adapter/simulate
```

Supported simulated events are `JOB_STARTED`, `PROGRESS`, `INTERRUPTED` and `JOB_COMPLETED`. The endpoint persists them as `ADAPTER_<EVENT>` records with source `simulated_adapter`, which makes them visible in the normal timeline and raw event export. Unsupported event types return `INVALID_ADAPTER_EVENT`; unknown jobs return `JOB_NOT_FOUND`.

This interface is intentionally simulated. It does not communicate with a printer, RIP or hot folder and does not claim certified physical-position accuracy.

## Verification

```bash
python3 test_simulated_adapter.py
```

The focused test verifies event production, response metadata, database persistence, invalid event validation and missing-job handling.
