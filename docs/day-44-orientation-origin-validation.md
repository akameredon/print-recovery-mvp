# Day 44 — Image orientation and origin validation

## Purpose

Day 44 adds explicit validation for the image orientation and declared media origin before assisted recovery review. New job manifests store an orientation value, with `top-left` as the backward-compatible default. Supported orientations are `top-left`, `top-right`, `bottom-left` and `bottom-right`.

The validation endpoint is:

```text
GET /api/jobs/<job_id>/orientation
```

It compares the source image dimensions with the declared media dimensions, checks that the orientation is supported and reports origin and aspect-ratio warnings. The result is one of `verified`, `warning` or `invalid`.

| Condition | Result |
|---|---|
| Supported orientation, positive dimensions, origin in range and compatible aspect ratio | `verified` |
| Origin outside the declared media or material aspect-ratio mismatch | `warning` |
| Unsupported orientation or invalid dimensions | `invalid` |

Warnings do not silently modify the source image or generate a continuation. They are evidence for operator review. The feature does not prove the physical printer’s origin or orientation after an interruption.

## Verification

```bash
python3 test_orientation_validation.py
```

The focused test covers verified metadata, aspect-ratio and origin warnings, invalid orientation handling, migration persistence and API output. The complete non-destructive regression suite, Black and Ruff checks pass.
