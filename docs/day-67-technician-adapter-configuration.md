# Day 67 — Technician-Only Adapter Configuration

**Status:** Implemented and verified  
**Roadmap day:** 67  
**Scope:** Protected adapter-boundary configuration for each shop workspace

## Delivered

Day 67 adds durable adapter configurations through schema migration 12. Each record is scoped to a workspace and stores an adapter name, supported adapter type, connection mode, trace file or endpoint, structured non-secret settings, status and enabled flag. Supported adapter types are the generic RIP observer, simulated adapter and hot-folder observer. Supported connection modes are trace file, hot-folder and observed queue.

The API supports listing, creating, updating and retiring adapter configurations. Mutating operations require an authenticated **technician** or **owner** session. Operators can list configurations for review but receive `403 ROLE_FORBIDDEN` when attempting to change them. Configuration records are audited through the Day 64 audit log.

The dashboard adds an adapter-configuration panel. It exposes the configuration boundary and status while explicitly stating that the form does not control hardware. The form accepts JSON settings but rejects keys that indicate passwords, secrets, tokens, API keys or private keys.

| Capability | Day 67 status |
|---|---|
| Workspace-scoped adapter records | Implemented |
| Generic, simulated and hot-folder adapter types | Implemented |
| Trace-file, hot-folder and observed-queue modes | Implemented |
| Technician/owner mutation gate | Implemented |
| Operator read-only visibility | Implemented |
| Secret-key rejection | Implemented |
| Create/update/retire audit events | Implemented |
| Direct printer control | Not implemented |
| Automatic recovery certification | Not claimed |

## Safety and security boundary

Adapter configuration defines a validated observation boundary; it does not execute vendor commands, bypass printer protections or certify physical position. The MVP continues to use assisted recovery. Secrets are intentionally excluded from this local configuration surface and must not be entered into its settings JSON.

## Verification evidence

The focused `test_adapter_configurations.py` test passed technician creation and update, operator blocking, safe settings persistence, secret rejection, workspace scoping, retirement and dashboard rendering. Migration and diagnostics tests passed through schema version 12.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, permissions, audit-log, workspace, profile, dashboard, observer, trace and usability tests remained passing.
