# Day 14 — Source-file integrity verification

## Purpose

A recovery decision is only trustworthy when the original source file has not been silently replaced or modified. Day 14 adds a read-only verification endpoint that compares the current source file with the SHA-256 digest recorded when the job was created.

## Endpoint

```text
GET /api/jobs/<job_id>/integrity
```

The endpoint returns `200` with `status: verified` when the source file exists and its digest matches. It returns `409` with `error: SOURCE_CHANGED` when the file exists but its digest differs, and `404` with `error: SOURCE_MISSING` when the recorded file cannot be found. Unknown jobs continue to use the standard `JOB_NOT_FOUND` response.

Each verification creates an append-only event: `SOURCE_VERIFIED`, `SOURCE_CHANGED` or `SOURCE_MISSING`. The endpoint never overwrites the recorded digest and never changes the job status, so an operator must explicitly decide what to do after a mismatch.

## Example successful response

```json
{
  "actual_hash": "...",
  "expected_hash": "...",
  "file_name": "banner.png",
  "job_id": "abc123",
  "status": "verified"
}
```

## Verification

The focused test covers all three source states and checks the corresponding event sequence:

```bash
python3 test_integrity.py
```

The test also confirms that a supplied `X-Correlation-ID` is preserved in the changed-file error response. This feature is an integrity safeguard for assisted recovery; it is not yet a certified printer or RIP adapter.
