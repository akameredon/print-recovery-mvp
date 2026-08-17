# Day 56 — Generic RIP observer adapter

## Purpose

Day 56 adds the first vendor-neutral RIP observer adapter. `rip_observer.py` reads a JSON Lines trace, preserves each raw record, validates the lifecycle sequence through the Day 54 observer, and returns a normalized observation without mutating the database or controlling a printer.

The adapter accepts lifecycle records such as `JOB_STARTED`, `PROGRESS`, `INTERRUPTED` and `JOB_COMPLETED`. Malformed JSON records are reported with their line number, unknown lifecycle events are rejected by the shared observer, and events after terminal states remain invalid.

| Adapter behavior | Result |
|---|---|
| Valid JSON Lines lifecycle trace | Returns ordered events and final lifecycle state |
| Malformed JSON line | Returns `INVALID_JSON` with line number and marks observation invalid |
| Unknown lifecycle event | Preserves the trace but reports an invalid lifecycle observation |
| Event after completion or interruption | Rejects the transition as unsafe |
| Real vendor connection | Not claimed; the adapter is a read-only trace boundary for future vendor integration |

The command-line entry point is:

```bash
python3 rip_observer.py /path/to/rip-trace.jsonl
```

This adapter is intentionally compatible with a future confirmed Mimaki/RasterLink6 trace export or hot-folder observer, but it does not infer physical printer position from host or RIP events.

## Verification

```bash
python3 test_rip_observer.py
```

The focused test verifies valid trace parsing, ordered completion, raw payload preservation, malformed-record rejection, terminal-state validation and read-only behavior. The complete non-destructive regression suite, Black and Ruff checks pass.
