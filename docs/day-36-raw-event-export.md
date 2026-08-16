# Day 36 — Raw event payload retention and export

## Purpose

Day 36 makes the exact serialized event payload available for adapter diagnostics. Events continue to retain their raw JSON string in SQLite, while the new endpoint exports the stored value without decoding and re-encoding it.

```text
GET /api/jobs/<job_id>/events/raw
```

The response is newline-delimited JSON (`application/x-ndjson`). Each record includes event metadata and a `payload_raw` string. The download filename is `<job_id>_raw_events.jsonl`. Invalid formats return `INVALID_RAW_EVENT_FORMAT`; unknown jobs return `JOB_NOT_FOUND`.

The dashboard includes a **Download raw events** link on each job card. This export is intended for adapter and incident diagnostics; the normal timeline remains the operator-friendly decoded view.

## Verification

```bash
python3 test_raw_event_export.py
```

The focused test verifies exact payload preservation, JSONL headers and filename, invalid-format handling, missing-job handling and dashboard access. The complete executable regression suite passed after the endpoint was corrected to emit real JSONL line delimiters.
