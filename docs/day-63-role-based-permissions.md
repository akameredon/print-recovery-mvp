# Day 63 — Role-Based Permissions for Recovery Overrides

**Status:** Implemented and verified  
**Roadmap day:** 63  
**Scope:** Protect technician-level printer-profile changes from operator accounts

## Delivered

Day 63 adds a reusable role gate for privileged configuration changes. Printer-profile creation, update and retirement now require an authenticated **technician** or **owner** session. Read-only profile listing and detail retrieval remain available for operational visibility.

An unauthenticated request receives `401 AUTHENTICATION_REQUIRED`. An authenticated operator attempting to change a printer profile receives `403 ROLE_FORBIDDEN`. Technician and owner sessions may perform the protected changes. The rule is applied server-side, so it does not depend on dashboard controls being present or hidden.

| Action | Operator | Technician | Owner |
|---|---:|---:|---:|
| List/view printer profiles | Allowed | Allowed | Allowed |
| Create printer profile | Denied | Allowed | Allowed |
| Update printer profile | Denied | Allowed | Allowed |
| Retire printer profile | Denied | Allowed | Allowed |

## Safety boundary

The permission gate protects configuration changes; it does not certify a printer, authorize automatic hardware control or replace physical validation. Profiles remain `assisted_only`, and the system continues to treat exact physical printer position as an evidence requirement rather than an assumption.

## Verification evidence

The focused profile regression test now authenticates a technician, creates multiple profiles, switches to an operator and verifies that the operator receives `ROLE_FORBIDDEN`, then returns to the technician and verifies update and retirement. Unsafe recovery modes and duplicate profile names remain rejected.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, profile, dashboard, observer, trace and usability tests remained passing.
