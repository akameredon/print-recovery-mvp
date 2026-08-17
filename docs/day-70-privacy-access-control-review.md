# Day 70 — Privacy and Access-Control Review

**Status:** Implemented and verified  
**Roadmap day:** 70  
**Scope:** Review and harden multi-user privacy and access boundaries

## Review findings and fixes

The review identified three privacy boundaries that needed tightening. Unauthenticated callers could previously list users and active workspaces. Audit-log queries were authenticated but were not explicitly scoped to the actor’s workspace. Account creation accepted workspace identifiers without a clear rule for authenticated users.

| Finding | Severity | Fix | Verification |
|---|---:|---|---|
| User listing available without authentication | High | `GET /api/users` now requires an authenticated session and returns only the active workspace’s users | Focused privacy test |
| Workspace listing disclosed all active shops | High | `GET /api/workspaces` now requires authentication and returns only the active workspace | Focused privacy test |
| Audit records lacked explicit workspace scope | High | Audit queries now constrain actor users to the authenticated workspace | Audit and full regression tests |
| Non-owner cross-workspace account assignment | High | Non-owners cannot assign accounts to another workspace; owners may administer workspace assignment | Focused privacy test and workspace regression |
| Default-workspace bootstrap compatibility | Deliberate boundary | Unauthenticated account creation remains available only for the default workspace to preserve local first-start bootstrap; non-default workspace account creation requires authentication | Privacy and account tests |

## Current access matrix

| Surface | Unauthenticated | Operator/technician | Owner |
|---|---|---|---|
| User list | Blocked | Active workspace only | Active workspace only |
| Workspace list | Blocked | Active workspace only | Active workspace only |
| Audit log | Blocked | Active workspace only | Active workspace only |
| Create same-workspace account | Default bootstrap only | Same workspace | Same workspace or selected workspace |
| Assign account to another workspace | Blocked | Blocked | Allowed |
| Owner outcomes | Blocked | Blocked | Active workspace only |
| Job detail and mutations | Blocked by route/session boundary | Active workspace and role rules | Active workspace and role rules |

## Residual limitations

The review does not claim production identity management, external directory integration, rate limiting, encrypted local secrets or network isolation. Those remain separate roadmap items. The default-workspace bootstrap is intentionally retained for a local installation, but production deployment should provision an owner through a controlled setup process before exposing the service.

The application continues to use assisted recovery. Access control prevents unauthorized application actions; it does not prove printer position, certify recovery or replace operator confirmation.

## Verification evidence

The focused `test_privacy_access_control.py` test passed unauthenticated listing blocks, workspace-scoped visibility and non-owner cross-workspace account-assignment denial. The legacy local-account regression also passed after its authenticated listing step was aligned with the new boundary.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, audit-log, workspace, profile, adapter, outcomes, conflict, dashboard, observer, trace and usability tests remained passing.
