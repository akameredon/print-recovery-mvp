# Day 2 — Structured Application Logging

**Roadmap day:** 2  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now writes structured JSON log records to `data/print_recovery.log` and standard output. Each record contains a UTC timestamp, severity, module name, message and correlation ID. Request records also include route, HTTP status and duration. Domain records include job ID and event type where applicable.

The application accepts an optional `X-Correlation-ID` request header. If none is supplied, it generates a new identifier. The identifier is returned in the response header and remains attached to all log records created during that request.

Interruption events are logged at warning level. Unexpected exceptions are logged with stack traces and return a safe API error containing the correlation ID for support diagnostics.

## Verification evidence

The normal MVP smoke test passed after the logging change. A focused logging test confirmed that a supplied correlation ID is returned and that the newest request log is valid JSON with timestamp, severity, module and correlation ID fields.

## Limitation

The current log file is local and has no rotation, centralized collection or privacy redaction policy beyond the application’s current payload choices. Those improvements belong to later roadmap days.
