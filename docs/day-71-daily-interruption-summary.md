# Day 71 — Daily Interruption Summary

**Status:** Implemented and verified  
**Roadmap day:** 71  
**Scope:** Workspace-scoped daily interruption reporting

## Delivered

Day 71 adds `GET /api/reports/daily-interruptions`. Authenticated technicians and owners can request a report for a specific UTC date using `YYYY-MM-DD`; when omitted, the report defaults to the current UTC date. The endpoint reads canonical interruption events and groups them by reason, classification and source.

Each report also includes the number of interruption events, affected jobs, current statuses of affected jobs and a detailed interruption list containing the job ID, file name, event timestamp, event type, source, reason, classification and operator note.

| Report field | Definition |
|---|---|
| Interruption events | Stored interruption event payloads with a canonical reason |
| Affected jobs | Distinct workspace jobs represented in the day’s interruption events |
| By reason | Counts grouped by the interruption reason vocabulary |
| By classification | Counts grouped by the classification matrix result |
| By source | Counts grouped by operator, adapter or other event source |
| Current job statuses | Current status of each affected job at report generation time |

## Dashboard workflow

The dashboard includes a **Daily interruption summary** panel for technicians and owners. A date can be selected and loaded without leaving the operator dashboard. Operators see a clear permission message rather than the report data.

## Safety and measurement boundary

The report summarizes software-observed events. It does not prove the electrical cause of an outage, the physical state of the printer, the exact amount of media consumed or the accuracy of a physical continuation boundary. The API and dashboard display this boundary explicitly.

Workspace isolation from Day 65 is enforced, and the report endpoint returns only events joined to jobs in the authenticated user’s active workspace. Invalid dates return `400 INVALID_DAILY_REPORT_QUERY`.

## Verification evidence

The focused `test_daily_interruptions.py` test passed interruption creation, daily grouping, affected-job counting, reason and classification aggregation, date validation, workspace scoping, operator blocking and dashboard rendering.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, privacy, audit-log, workspace, profile, adapter, outcomes, conflict, dashboard, observer, trace and usability tests remained passing.
