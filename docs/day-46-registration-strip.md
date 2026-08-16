# Day 46 — Registration-strip generation

## Purpose

Day 46 adds registration-strip generation for assisted recovery review. The strip crops a configurable physical-height window around the selected recovery coordinate and overlays a red border, a red seam line and a blue center marker. A coordinate label is included in the generated image.

The API is:

```text
POST /api/jobs/<job_id>/registration-strip
```

The request accepts `y_mm` and an optional `strip_height_mm`. If the height is omitted, the job’s configured overlap provides a conservative default. Each generated strip receives a unique versioned filename containing the job ID, source-hash token and selected coordinate. The response includes the output URL, crop boundaries, version, source hash and an explicit operator-confirmation requirement.

Each generation is recorded as a `REGISTRATION_STRIP_GENERATED` event. The feature generates a review aid only; it does not send data to a printer, certify registration or automatically authorize continuation.

## Verification

```bash
python3 test_registration_strip.py
```

The focused test verifies rendered image delivery, crop boundaries, version 1 and version 2 outputs, source-hash traceability, persisted event metadata and invalid-coordinate handling. The complete non-destructive regression suite, Black and Ruff checks pass.
