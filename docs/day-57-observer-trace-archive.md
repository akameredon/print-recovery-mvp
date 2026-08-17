# Day 57 — Observer trace archive and replay verification

## Purpose

Day 57 adds a deterministic archive format for observer traces. `trace_archive.py` stores the raw ordered events, the normalized lifecycle observation, source identifier, archive timestamp and a SHA-256 digest over the canonical archive content.

The archive can be replayed without a database or printer. Replay recalculates the digest and runs the same lifecycle observer over the stored events. The result reports both `hash_verified` and `replay_matches`, making later evidence review explicit about whether the file was altered and whether the recorded interpretation is reproducible.

| Check | Meaning |
|---|---|
| Archive schema | Identifies the versioned observer-trace format |
| Canonical SHA-256 | Detects changes to archive content |
| Replayed observation | Confirms deterministic lifecycle interpretation |
| Raw event preservation | Keeps the original progress and queue payloads for review |
| Tamper result | A modified event fails both hash and replay comparison |

The archive is a software evidence artifact. It does not certify physical printer position or replace operator review.

## Verification

```bash
python3 test_trace_archive.py
```

The focused test verifies archive creation, digest generation, deterministic replay, raw-event preservation and tamper detection. The complete non-destructive regression suite, Black and Ruff checks pass.
