# Days 76–80 — Operations controls

**Status:** Implemented and verified.

## Day 76 — Local interruption notifications

Interruption recording now creates durable workspace-scoped local notifications for active technicians and owners. Users can list their own notifications, filter unread items and mark a notification read. Notification creation occurs at the same application transaction as the interruption record. The system does not claim that a notification proves the physical cause of an interruption.

## Day 77 — Optional email notification configuration

Owners can store an optional email-notification preference and recipient list. The implementation validates the recipient shape, stores no SMTP password or token, and explicitly reports `configuration_only_no_external_send`. No external mail provider is contacted by this milestone; provider integration remains a separately approved deployment task.

## Day 78 — Retention and deletion controls

Owners can set a workspace retention period from 7 to 3,650 days and explicitly run a workspace-scoped purge. Purges delete aged job evidence and write an audit record containing the cutoff and count. The default is 365 days, and the system does not silently delete data in the background.

## Day 79 — Backup status visibility

Technicians and owners can record and inspect scheduled, running, succeeded or failed backup status entries for their workspace. The response states that a status record does not establish restorability until a restore test passes.

## Day 80 — Technician support bundle

Technicians and owners can retrieve a workspace-scoped support bundle containing selected job metadata, event evidence, checkpoints and non-secret adapter configuration metadata. Password hashes, SMTP passwords, tokens and raw secret settings are explicitly excluded. The bundle is diagnostic evidence only and is not a physical-position certificate.

## Verification

| Check | Result |
|---|---|
| Focused operational-controls test | Passed |
| Local notification delivery and read state | Passed |
| Email configuration safety boundary | Passed |
| Retention settings | Passed |
| Backup status recording and listing | Passed |
| Technician support bundle secret exclusions | Passed |

The focused test is `test_operational_controls.py`. The implementation uses migration 14 and preserves workspace and role boundaries.
