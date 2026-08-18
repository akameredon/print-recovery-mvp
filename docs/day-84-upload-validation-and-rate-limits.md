# Day 84 — Upload validation and rate limits

**Status:** Implemented and verified.

Day 84 strengthens the job-upload boundary. Uploads now require an allowed source extension (`png`, `jpg`, `jpeg`, `tif`, `tiff` or `webp`) and an allowed image-oriented MIME type. Path components are reduced to a safe basename, configured request and post-save size limits are enforced, and rejected oversized files are removed from disk.

A rolling per-client upload limit is applied before persistence. The default is 100 uploads per minute and can be configured through `PRINT_RECOVERY_UPLOAD_RATE_LIMIT_PER_MINUTE`. A rejected request returns HTTP 429 with `UPLOAD_RATE_LIMITED` and a `Retry-After` header. The existing Flask maximum request size remains active as a second boundary.

The validation deliberately checks transport metadata and size rather than decoding every uploaded file at the upload boundary, preserving the project’s existing assisted workflow and synthetic fixture compatibility. Image decoding remains required by image-processing operations such as previews and continuation generation.

| Verification | Result |
|---|---|
| Invalid extension rejection | Passed |
| Invalid MIME rejection | Passed |
| Oversize policy implementation | Passed |
| Per-client rate limiting | Passed |
| Retry-After response header | Passed |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 72 tests |

The focused regression test is `test_upload_validation.py`.
