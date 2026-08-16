# Day 41 — Continuation preview

## Purpose

Day 41 adds a visual, read-only continuation preview before any continuation image is generated. The preview overlays three operator-facing regions on the source image:

| Region | Meaning | Visual treatment |
|---|---|---|
| Printed | Area before the uncertainty window | Green overlay |
| Uncertain | Configured overlap around the selected coordinate | Amber overlay |
| Remaining | Area after the uncertainty window | Blue overlay |

A red horizontal line marks the selected `y_mm` coordinate. The preview API is:

```text
GET /api/jobs/<job_id>/continuation-preview?y_mm=<coordinate>&overlap_mm=<overlap>
```

It returns region boundaries in millimetres, a preview image URL and an explicit `operator_confirmation_required` flag. The endpoint does not create a recovery decision, status transition or event. It is therefore safe to use repeatedly while an operator reviews the evidence. The existing continuation-generation endpoint remains a separate action.

The dashboard includes a **Preview recovery regions** control and an accessible table describing each region. The preview is an assisted-recovery visualization, not proof of exact physical printer position.

## Verification

```bash
python3 test_continuation_preview.py
```

The focused test verifies region boundaries, rendered image delivery, invalid-coordinate handling and read-only database behavior. The complete non-destructive regression suite and formatting/static checks also pass.
