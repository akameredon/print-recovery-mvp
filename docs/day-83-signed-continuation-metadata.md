# Day 83 — Signed continuation metadata

**Status:** Implemented and verified.

Day 83 adds signed metadata to every generated continuation output. The metadata binds the continuation to its job ID, output filename, version, source hash, selected coordinate, overlap and generation timestamp. It is signed with an HMAC derived from the protected local key introduced in Day 82.

The generation response includes `signed_metadata` and `metadata_signature`. The durable `CONTINUATION_GENERATED` event retains the existing top-level fields for compatibility and adds the signed metadata payload. The read-only endpoint `/api/jobs/<job_id>/continuation-metadata?file=...` verifies the signature and returns `verified` or rejects a tampered record with HTTP 409.

Missing metadata queries, unknown files and tampered payloads are handled explicitly. Verification confirms metadata integrity; it does not certify physical printer position, print quality or continuation safety. Existing recovery safety gates still run before any continuation is generated.

| Verification | Result |
|---|---|
| Signed metadata generation | Passed |
| Signature verification | Passed |
| Tampered metadata not accepted | Passed |
| Legacy event fields preserved | Passed |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 71 tests |

The focused regression test is `test_continuation_metadata_signature.py`.
