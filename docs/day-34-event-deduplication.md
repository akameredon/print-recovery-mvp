# Day 34 — Duplicate event suppression

## Purpose

Day 34 prevents repeated identical domain events from filling the recovery timeline when a printer, RIP or operator repeats the same status message. Before inserting an event, the application compares it with the most recent event for that job using the event type, source and canonical JSON payload.

If all three values match, the new event is suppressed and the existing event remains the durable record. Payload keys are serialized in sorted order so equivalent dictionaries compare consistently. A changed note, reason, source or event type creates a new event as expected.

This is consecutive-event deduplication, not global history deletion. Earlier identical events remain part of the audit history if a different event occurred between them.

## Verification

```bash
python3 test_event_deduplication.py
```

The focused test records the same interruption twice and confirms that only one event is stored, then changes the operator note and confirms that the distinct event is preserved. The complete executable regression suite passed, with the process-kill durability test run separately because it intentionally terminates the Flask process.
