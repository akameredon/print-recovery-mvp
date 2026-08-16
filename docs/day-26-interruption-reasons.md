# Day 26 — Interruption reason selector and notes

## Purpose

Day 26 makes interruption records more useful to operators by requiring a structured reason vocabulary while retaining a free-text note for incident context.

## Supported reasons

| Reason | Intended use |
|---|---|
| `POWER_LOSS` | Utility power outage or unstable supply. |
| `PROTECTION_TRIP` | Lightning or safety-protection trip. |
| `COMMUNICATION_LOSS` | Lost connection between host/RIP and printer. |
| `PRINTER_ERROR` | Printer-reported fault or alarm. |
| `MATERIAL_ISSUE` | Media, ink or material problem. |
| `OPERATOR_ABORT` | Deliberate operator stop. |
| `UNKNOWN` | Cause is not yet known. |

The API remains:

```text
POST /api/jobs/<job_id>/interrupt
```

A request may include `reason`, `source` and an optional `note` of up to 1,000 characters. The reason and note are saved in the event payload, while the event type remains available for existing status-history and timeline consumers. The dashboard exposes the same reason selector and note field.

Invalid reasons return `INVALID_INTERRUPTION_REASON` with HTTP 400. Notes longer than 1,000 characters return `INVALID_INTERRUPTION_NOTE`. Unknown jobs return `JOB_NOT_FOUND`. The route does not authorize recovery or printing; it records evidence and marks the interruption through the existing assisted-recovery workflow.

## Verification

```bash
python3 test_interruption_reasons.py
```

The test verifies protection-trip recording, structured event payloads, note persistence, invalid reason handling, overlong note handling, missing-job handling and dashboard controls. The complete executable regression suite passed after the change.
