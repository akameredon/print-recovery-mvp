# Day 38 — Event replay tool

## Purpose

Day 38 adds `event_replay.py`, a read-only command-line tool for reconstructing a job's recorded timeline during diagnostics. It reads status transitions, checkpoints, events and operator decisions from SQLite, normalizes them into one timeline and sorts them by timestamp with deterministic tie-breakers.

Usage:

```bash
python3 event_replay.py --db data/print_recovery.sqlite3 --job-id <JOB_ID>
```

The command emits JSON containing the job identifier, item count and replay items. Raw event payloads are retained as `payload_raw`; the tool does not apply recovery actions, alter checkpoints or write to the database. An unknown job fails with `JOB_NOT_FOUND`.

## Verification

```bash
python3 test_event_replay.py
```

The focused test verifies chronological reconstruction, inclusion of checkpoint and adapter-event records, raw payload preservation, unknown-job handling and byte-for-byte database immutability.
