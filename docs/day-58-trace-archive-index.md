# Day 58 — Trace archive index and retrieval

## Purpose

Day 58 adds a deterministic index over versioned observer-trace archives. `trace_index.py` scans a selected archive directory, ignores unrelated JSON files, replays each valid archive, and returns searchable metadata without modifying evidence files.

The retrieval layer supports filtering by observer source, final lifecycle state and `verified_only`. Verified-only results require both the archive hash and deterministic replay to match. Entries are sorted deterministically by archive timestamp and path so repeated reviews produce stable ordering.

| Index field | Meaning |
|---|---|
| Archive path | Location of the immutable evidence file |
| Source and archived time | Provenance and chronological review context |
| SHA-256 status | Whether archive content matches its stored digest |
| Replay status | Whether recorded interpretation is reproducible |
| Final state and event count | Fast lifecycle triage metadata |

The index is intentionally read-only. It does not delete, rewrite or silently repair a trace archive; modified or invalid evidence is surfaced through its verification fields and excluded when `verified_only=True`.

## Verification

```bash
python3 test_trace_index.py
```

The focused test verifies two-archive indexing, deterministic ordering, source and final-state filters, verified-only filtering and ignoring unrelated JSON files. The complete non-destructive regression suite, Black and Ruff checks pass.
