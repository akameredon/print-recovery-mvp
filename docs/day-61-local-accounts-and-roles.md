# Day 61 — Local User Accounts and Roles

**Status:** Implemented and verified  
**Roadmap day:** 61  
**Scope:** Local account identity and role selection

## Delivered

Day 61 adds a durable `users` table through schema migration 7. Each local account has a unique username, display name, active flag, creation timestamp and one of three supported roles: **operator**, **technician** or **owner**.

The application now exposes account and session endpoints. `GET /api/users` lists local accounts and supported roles, `POST /api/users` creates an account, `GET /api/session` reports the current selected account, `POST /api/session` selects an active account, and `DELETE /api/session` clears the local selection. The selected account is held in the Flask session and is shown in the dashboard.

The dashboard includes a local-account panel where a shop can create accounts and select the active role. This makes the three role identities visible and usable without pretending that authorization is complete. Role-based permissions for overrides are intentionally scheduled for Day 63.

## Safety and security boundary

Day 61 establishes local identity and role context only. It does **not** claim password security, password hashing, session expiry, account recovery, or permission enforcement. Password hashing and session expiry are scheduled for Day 62, while role-based permissions are scheduled for Day 63. The dashboard states this boundary directly so that account selection is not mistaken for production authentication.

| Capability | Day 61 status |
|---|---|
| Durable local account record | Implemented |
| Operator, technician and owner roles | Implemented |
| Active-account selection | Implemented |
| Session-visible current user | Implemented |
| Password hashing | Not yet implemented; Day 62 |
| Session expiry | Not yet implemented; Day 62 |
| Role-based override permissions | Not yet implemented; Day 63 |

## Verification evidence

The focused `test_local_users.py` regression test passed creation and retrieval for all three roles, duplicate-username rejection, invalid-role rejection, session selection and dashboard rendering. The migration test passed schema versions 1 through 7 and idempotent reruns, and the diagnostics test passed with the new schema version.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, observer, trace, dashboard and usability tests remained passing.
