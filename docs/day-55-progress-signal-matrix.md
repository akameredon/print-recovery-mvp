# Day 55 — Progress-signal evidence matrix

## Purpose

Day 55 adds a signal matrix that records which progress signals are actually available and what each signal can safely prove. The matrix separates host, RIP, printer and physical evidence instead of treating all progress messages as equivalent.

| Signal family | Example signals | Conservative implication |
|---|---|---|
| Host | Job created, transmission started or completed | Identifies host-side progress but does not prove printer or media position |
| RIP | Queue seen, RIP progress percentage | Shows RIP observation or progress; buffering and seam position remain uncertain |
| Printer | Device status feedback | Adds device evidence but still requires coordinate validation |
| Physical | Durable physical checkpoint | Strongest available evidence, while remaining subject to target-specific validation |

The API is:

```text
POST /api/jobs/<job_id>/signals/assess
```

It returns the available families, a row for every known signal, the conservative recovery mode and a confidence limitation. The assessment is persisted as a `SIGNAL_MATRIX_ASSESSED` event with the source and observed signal list.

This matrix is an evidence contract for the upcoming real RIP observer work. It does not infer missing printer signals and does not convert host progress into certified physical completion.

## Verification

```bash
python3 test_signal_matrix.py
```

The focused test verifies all four evidence families, recovery-mode selection, API output, raw persistence and invalid input handling. The complete non-destructive regression suite, Black and Ruff checks pass.
