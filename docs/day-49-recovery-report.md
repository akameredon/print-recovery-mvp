# Day 49 — Recovery report with selected coordinate and confidence

## Purpose

Day 49 adds a recovery report that consolidates the evidence required for an assisted continuation review. The report includes the selected coordinate, overlap, checkpoint confidence, source-file integrity, interruption classification, operator review, decision data and structured recovery-safety blockers.

The endpoint is:

```text
GET /api/jobs/<job_id>/recovery-report
```

The default response is JSON. A Markdown version is available with `?format=md` and is suitable for saving, attaching to a job record or reviewing with a technician. The report is generated from recorded job data and does not create a decision or continuation output.

| Report section | Meaning |
|---|---|
| Selected coordinate | The latest recovery decision coordinate, or the latest checkpoint when no decision exists |
| Confidence | Transparent checkpoint score, level and factors |
| Source integrity | Comparison of the current source hash with the job manifest |
| Interruption | Latest recorded interruption reason, note and classification |
| Operator review | Latest approval or rejection event when present |
| Recovery safety | Blockers and warnings that control whether generation is safe to attempt |

The report explicitly states that it organizes evidence for assisted recovery and does not certify exact physical printer position.

## Verification

```bash
python3 test_recovery_report.py
```

The focused test verifies JSON and Markdown delivery, selected-coordinate capture, medium confidence calculation, interruption classification, operator-review evidence, safety status and invalid-format handling. The complete non-destructive regression suite, Black and Ruff checks pass.
