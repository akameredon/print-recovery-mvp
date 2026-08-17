# Day 65 — Shop/Workspace Separation

**Status:** Implemented and verified  
**Roadmap day:** 65  
**Scope:** Isolate jobs by shop workspace

## Delivered

Day 65 adds durable workspaces through schema migration 11. The migration creates a default `ws-default` workspace for existing installations, adds `workspace_id` to users and jobs, and creates lookup indexes for both relationships.

New users can be assigned to a validated workspace. An authenticated owner can create additional workspaces through `POST /api/workspaces`, and active workspaces can be listed through `GET /api/workspaces`. Login responses and the dashboard user context expose the active user’s workspace.

New jobs inherit the authenticated user’s workspace. Job lists filter by the active workspace, and a request-level boundary prevents a user from accessing a job belonging to another workspace. A cross-workspace job behaves as not found rather than revealing its existence.

| Capability | Day 65 status |
|---|---|
| Durable workspace records | Implemented |
| Default workspace migration for existing data | Implemented |
| Assign users to workspaces | Implemented |
| Create/list workspaces | Implemented |
| Assign new jobs to active workspace | Implemented |
| Filter job lists by workspace | Implemented |
| Block cross-workspace job access | Implemented |
| Physical printer separation | Not claimed; this is application-level isolation |

## Security and safety boundary

Workspace separation is an application-level access boundary. It does not claim that two shops are physically isolated at the operating-system, network or printer level. Printer profiles and audit-log scoping remain later hardening areas; the Day 65 acceptance boundary is job isolation by shop workspace.

A missing or cross-workspace job returns `404 JOB_NOT_FOUND`, avoiding cross-shop existence disclosure. Existing jobs are assigned to the default workspace by migration, preserving data while establishing a deterministic scope.

## Verification evidence

The focused `test_workspaces.py` test passed workspace creation, user assignment, job ownership, active-workspace listing and cross-workspace blocking. Migration and diagnostics tests passed through schema version 11.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, audit-log, profile, dashboard, observer, trace and usability tests remained passing.
