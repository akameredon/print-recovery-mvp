# Day 13 — Status-History Export

**Roadmap day:** 13  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now exposes a read-only export endpoint:

```text
GET /api/jobs/<job_id>/status-history/export?format=json
GET /api/jobs/<job_id>/status-history/export?format=csv
```

JSON exports contain the job ID, total count, format marker and complete ordered history items. CSV exports contain stable columns for transition ID, job ID, previous status, new status, reason, source and timestamp. Both formats use a safe job-specific download filename.

The endpoint accepts only `json` or `csv`. Unsupported formats return `INVALID_EXPORT_FORMAT`; missing jobs return `JOB_NOT_FOUND` using the standard error contract.

## Verification evidence

The focused export test passed for JSON content and download headers, CSV content and headers, invalid-format validation and missing-job handling. The full status-history, migration, configuration, logging, diagnostics, error-handling and recovery regression suite also passed.

## Limitation

Exports contain the software’s recorded lifecycle evidence. They do not establish that the printer physically reached a position or that a continuation job is safe to run without operator review.
