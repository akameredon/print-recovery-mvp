# Day 72 — Weekly Material-Waste Report

**Status:** Implemented and verified  
**Roadmap day:** 72  
**Scope:** Owner-only weekly recovery outcome reporting

## Delivered

Day 72 adds `GET /api/reports/weekly-material-waste`. The endpoint accepts an optional Monday `week_start` date in `YYYY-MM-DD` format and returns a seven-day inclusive reporting window. When omitted, the report uses the current UTC week starting Monday.

The report summarizes workspace recovery decisions, continuation and restart outcomes, estimated material saved, estimated waste, jobs created during the week and a printer/RIP breakdown. The breakdown helps owners compare recovery outcomes across the configured production workflows without claiming physical measurement.

| Metric | Definition |
|---|---|
| Jobs created | Workspace jobs created during the selected week |
| Decisions | Recovery decisions created during the selected week |
| Continuations | Decisions with `generated_continuation` action |
| Restarts | Decisions with a restart action |
| Estimated material saved | Declared media width multiplied by selected continuation coordinate |
| Estimated waste | Declared full job area for restart decisions |
| Printer/RIP breakdown | Decisions, continuations, restarts and estimates grouped by printer model and RIP |

## Access and dashboard workflow

The endpoint is restricted to authenticated owners and remains scoped to the owner’s active workspace. Operators and technicians receive `403 ROLE_FORBIDDEN`. The dashboard adds a **Weekly material-waste report** panel with week selection, summary output and printer/RIP detail.

## Safety and measurement boundary

The report is a management summary based on stored job dimensions and recovery decisions. Material saved and waste values are **software-recorded estimates**, not physical media measurements. They do not prove actual consumption, seam quality, electrical cause, physical printer position or certified recovery accuracy. The API and dashboard display this limitation explicitly.

## Verification evidence

The focused `test_weekly_material_waste.py` test passed week-range calculation, owner authorization, report metric structure, invalid-date handling, measurement-boundary wording and dashboard rendering.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, privacy, audit-log, workspace, profile, adapter, owner-outcomes, conflict, daily-report, dashboard, observer, trace and usability tests remained passing.
