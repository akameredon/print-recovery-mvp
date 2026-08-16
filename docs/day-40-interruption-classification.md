# Day 40 — Interruption classification test matrix

## Purpose

Day 40 classifies interruptions into distinct operational categories instead of treating every stop as an interchangeable error. The matrix is deliberately conservative: classification organizes evidence and review; it does not claim that software can infer exact physical printer state.

| Reason | Classification | Required evidence | Recovery implication |
|---|---|---|---|
| `POWER_LOSS` | Outage | Reason and last durable checkpoint | Review power restoration before assisted recovery |
| `PROTECTION_TRIP` | Outage | Trip reason and last durable checkpoint | Confirm safe restart after electrical protection event |
| `PRINTER_ERROR` | Crash | Device/RIP diagnostic note | Do not equate host progress with physical completion |
| `OPERATOR_ABORT` | Abort | Operator note | Review intentional stop before continuing |
| `COMMUNICATION_LOSS` | Communication loss | Last host transmission | Use assisted recovery and registration check |
| `MATERIAL_ISSUE` | Material issue | Operator note and media condition | Resolve media condition first |
| `UNKNOWN` | Unknown | Reason and operator review | Do not infer a safe continuation position |

The interruption endpoint now returns the classification and persists it inside the event payload. The existing interruption reason validation and mandatory operator confirmation remain unchanged.

## Verification

```bash
python3 test_interruption_classification.py
```

The focused matrix test covers all seven rows, unknown fallback behavior, API response output and event-payload persistence.
