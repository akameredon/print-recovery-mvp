# Day 12 — Paginated Status-History API

**Roadmap day:** 12  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now exposes `GET /api/jobs/<job_id>/status-history` as a dedicated lifecycle-history endpoint. It returns ordered history items together with `page`, `per_page`, `total`, `pages`, `has_next` and `has_previous` metadata.

The default page size is 25, and callers may request between 1 and 100 items per page. Invalid integer values or out-of-range values return the standard `INVALID_PAGINATION` error response. A missing job returns `JOB_NOT_FOUND` with the normal correlation-ID and JSON error contract.

## Example

```text
GET /api/jobs/abc123/status-history?page=1&per_page=25
```

The endpoint is intentionally read-only. It does not change job status or create new events.

## Verification evidence

The focused API test passed for a three-transition lifecycle, two-page pagination, stable chronological ordering, invalid pagination parameters and missing-job handling. The status-history unit test and the complete migration, configuration, logging, diagnostics, error-handling and recovery regression suite also passed.

## Limitation

Pagination improves retrieval of recorded software events; it does not increase the accuracy of physical printer-position detection. The history still represents software-observed transitions until a printer/RIP adapter supplies stronger evidence.
