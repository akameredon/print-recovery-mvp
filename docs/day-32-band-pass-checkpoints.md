# Day 32 — Logical band and pass checkpoint fields

## Purpose

Day 32 extends checkpoint evidence beyond a Y-coordinate by persisting an optional logical band number and pass number. This supports workflows where progress is tracked by raster band, print pass or both.

Migration 4 adds `logical_band` and `pass_number` columns to the `checkpoints` table. Existing checkpoints remain valid with null values, so the migration is backward compatible. New checkpoint requests may include integer values for either field:

```json
{
  "y_mm": 100,
  "evidence": "transmitted",
  "logical_band": 7,
  "pass_number": 2
}
```

The API response and `CHECKPOINT` event payload return and preserve the same values. Negative values are rejected, and non-integer values are invalid. The dashboard provides optional logical-band and pass-number inputs alongside the configured millimetre interval.

These fields describe recorded logical progress. They do not independently prove the physical printer position; physical confirmation remains a separate evidence level.

## Verification

```bash
python3 test_checkpoint_band_pass.py
```

The focused test verifies migration persistence, API response values, database columns, event evidence and dashboard controls. The complete executable regression suite passed after the migration and route changes.
