# Day 35 — Clock-source and timestamp consistency checks

## Purpose

Day 35 adds a clock diagnostic to the health and diagnostics responses. The application compares its UTC timestamp source with SQLite’s UTC timestamp source and reports the measured drift.

The diagnostic identifies both sources as `application_utc_and_sqlite_utc`, reports the two timestamps, the drift in seconds and a five-second warning threshold. Normal conditions return `status: ok` with the message `Clock sources are consistent`. Excessive drift returns `status: warning` with the message `Clock-source drift may affect event ordering`; the overall health response is then degraded so an operator can investigate before relying on fine-grained event order.

This check does not change recorded timestamps or attempt to correct the host clock. It makes a possible ordering problem visible. Time synchronization and host operating-system configuration remain deployment responsibilities.

## Verification

```bash
python3 test_clock_consistency.py
```

The focused test verifies the normal health and diagnostics fields and exercises a deliberately inconsistent application timestamp to confirm the warning state. The complete executable regression suite passed after the change; the process-kill durability test was run at the end of the suite because it intentionally terminates the Flask process.
