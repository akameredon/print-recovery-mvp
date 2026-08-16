# Day 50 — Full synthetic interruption test suite

## Purpose

Day 50 adds a repeatable local API scenario runner for the full assisted-recovery workflow. The runner creates isolated synthetic jobs, records durable checkpoints, injects interruption reasons, verifies the Day 40 classification matrix, generates a recovery report and exercises successful continuation generation.

It also verifies that the Day 48 safety rules block continuation when the checkpoint is missing or the source file has changed after capture. The suite does not claim physical printer accuracy; it validates software behavior and evidence handling.

## Scenario coverage

| Scenario | Expected result |
|---|---|
| Power loss | Classified as outage |
| Protection trip | Classified as outage |
| Printer error | Classified as crash |
| Operator abort | Classified as abort |
| Communication loss | Classified as communication loss |
| Material issue | Classified as material issue |
| Unknown interruption | Classified as unknown |
| Successful assisted recovery | Continuation output generated and traceable |
| Missing checkpoint | Continuation blocked with `CHECKPOINT_MISSING` |
| Changed source | Continuation blocked with `SOURCE_CHANGED` |

The archived JSON result is stored at `docs/verification/day-50-synthetic-interruptions.json`. It records the UTC generation time, scenario count, status and per-scenario result.

## Verification

```bash
python3 synthetic_interruptions.py \
  --report docs/verification/day-50-synthetic-interruptions.json
```

The Day 50 run passed all ten scenarios. The complete non-destructive regression suite, Black and Ruff checks also passed. The specialized process-kill durability test remains a separate final reliability check.
