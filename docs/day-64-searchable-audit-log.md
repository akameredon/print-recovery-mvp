# Day 64 — Searchable Audit Log

**Status:** Implemented and verified  
**Roadmap day:** 64  
**Scope:** Searchable audit records for authentication and configuration changes

## Delivered

Day 64 adds a durable `audit_log` table through schema migration 10. Each record stores the actor user ID, username and role when available, action, resource type, resource ID, structured details and UTC timestamp. Passwords are never written to audit details.

Authentication events now include successful login, failed login and logout. Printer-profile configuration changes record create, update and retire actions. Denied technician-level changes record a `PERMISSION_DENIED` event with the actor role. These records complement the existing job evidence and recovery-event history; they do not replace the job timeline.

The searchable `GET /api/audit-log` endpoint supports action, actor, resource type, free-text, date-range and bounded limit filters. It requires an authenticated session and returns structured JSON suitable for review or future reporting. The dashboard includes a search box, action filter and audit-record viewer.

| Capability | Day 64 status |
|---|---|
| Durable audit records | Implemented |
| Login success/failure and logout events | Implemented |
| Printer-profile configuration events | Implemented |
| Permission-denied records | Implemented |
| Search by action, actor, resource or details | Implemented |
| Date and bounded-limit filters | Implemented |
| Passwords in audit data | Prohibited |
| Searchable dashboard viewer | Implemented |

## Security and safety boundary

The audit log is an evidence and accountability surface. It does not grant permission, certify a printer position or authorize automatic hardware control. Authorization remains enforced by the Day 63 role gate, and all recovery remains assisted-only.

## Verification evidence

The focused `test_audit_log.py` test passed login success and failure recording, logout recording, profile creation/update/retirement events, searchable action and actor filters, password exclusion and unauthenticated access blocking. Migration and diagnostics tests passed through schema version 10.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, profile, permissions, dashboard, observer, trace and usability tests remained passing.
