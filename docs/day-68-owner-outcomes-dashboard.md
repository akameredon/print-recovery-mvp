# Day 68 — Owner Outcomes Dashboard

**Status:** Implemented and verified  
**Roadmap day:** 68  
**Scope:** Owner-only workspace metrics for material waste and recovery outcomes

## Delivered

Day 68 adds `GET /api/outcomes`, restricted to authenticated owners. The endpoint summarizes jobs, interruptions, recovery decisions, approved and rejected reviews, generated continuations, restart actions and test-first actions for the owner’s active workspace. Optional `date_from` and `date_to` filters use the job creation date and require `YYYY-MM-DD` values.

Material figures are calculated from stored job dimensions and recovery decisions. The dashboard reports total job area, estimated material saved area, estimated waste area, and square-metre conversions. The owner dashboard also renders the operational counts in a compact metric grid.

| Metric | Definition |
|---|---|
| Total jobs | Jobs in the owner’s active workspace and selected date range |
| Interrupted jobs | Distinct jobs with a stored `INTERRUPTED` event |
| Continuations generated | Decisions whose operator action contains `generated_continuation` |
| Estimated material saved | Job width multiplied by the selected continuation coordinate |
| Estimated waste | Full job area for decisions whose operator action contains `restart` |
| Approved/rejected reviews | Stored recovery-review events with the corresponding action |

## Safety and measurement boundary

The dashboard is an owner reporting surface, not a physical measurement instrument. Material saved and waste figures are software-recorded estimates derived from declared job dimensions and recovery decisions. They do not prove the quantity of media physically consumed, the quality of a seam or the exact physical printer position. The API includes this boundary in every response, and the dashboard displays it next to the metrics.

Operators and technicians cannot access the owner outcomes endpoint; they receive `403 ROLE_FORBIDDEN`. Workspace scoping is inherited from Day 65, so an owner sees only the jobs and events belonging to the owner’s active shop workspace.

## Verification evidence

The focused `test_owner_outcomes.py` test passed owner access, metric response structure, measurement-boundary wording, invalid date rejection, operator blocking and dashboard rendering. The complete non-restart regression suite passed with Black, Ruff and Python compilation.

The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, audit-log, workspace, profile, adapter, dashboard, observer, trace and usability tests remained passing.
