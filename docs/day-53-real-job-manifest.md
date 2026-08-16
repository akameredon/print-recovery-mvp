# Day 53 — Real-job manifest capture

## Purpose

Day 53 adds a canonical job-manifest endpoint for capturing host-side evidence about a real uploaded job without controlling the printer. The endpoint is:

```text
GET /api/jobs/<job_id>/manifest
```

The default JSON manifest records the manifest schema, capture time and mode, source path and expected hash, the live source hash, source-integrity status, printer/RIP metadata, media geometry, origin, overlap, scale, resolution, passes, profile and the assisted-only recovery mode. A Markdown representation is available with `?format=md` for technician review or attachment to a job record.

| Manifest evidence | Purpose |
|---|---|
| Expected and actual source hashes | Detect missing or changed source data at capture time |
| Printer/RIP fields | Preserve the job’s declared target metadata |
| Media and origin fields | Preserve coordinate interpretation inputs |
| Capture mode and timestamp | Distinguish host-side capture from printer control |
| Assisted-only mode | Prevent the manifest from being mistaken for certified recovery evidence |

The feature is ready for use with a real sample job, but no real printer/RIP capture is claimed in this repository checkpoint because that requires access to the target shop’s equipment and workflow.

## Verification

```bash
python3 test_job_manifest.py
```

The focused test verifies JSON and Markdown delivery, canonical schema, live source-hash verification, printer metadata and invalid-format handling. The complete non-destructive regression suite, Black and Ruff checks pass.
