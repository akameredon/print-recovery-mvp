# Day 31 — Configurable checkpoint interval by millimetres

## Purpose

Day 31 adds a configurable checkpoint interval for operators and future adapters. The default is `100.0` millimetres. The value can be set in `config.json` or through `PRINT_RECOVERY_CHECKPOINT_INTERVAL_MM`.

The dashboard uses the configured interval as the Y-coordinate input step and displays the active value beside the control. Each checkpoint response includes `checkpoint_interval_mm`, and the corresponding `CHECKPOINT` event payload records `interval_mm` so later reports can show which interval was active when the evidence was captured.

Example configuration:

```json
{
  "checkpoint_interval_mm": 50
}
```

The interval must be greater than zero. Invalid values are rejected during configuration loading. This setting controls the recommended recording granularity; it does not prove physical printer position and does not replace an adapter’s machine-specific telemetry.

## Verification

```bash
python3 test_checkpoint_interval.py
```

The focused test verifies the dashboard step value, checkpoint response, event payload and invalid-zero configuration handling. The complete executable regression suite passed after the feature was implemented.
