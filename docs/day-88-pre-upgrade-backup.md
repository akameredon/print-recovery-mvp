# Day 88 — Automatic database backup before upgrades

**Status:** Implemented and verified.

`upgrade_backup.py` adds a pre-upgrade backup wrapper around the existing checksummed archive format. It creates a timestamped `print-recovery-pre-upgrade-*.zip` archive, writes a manifest with file sizes and SHA-256 digests, and marks the result as a verified pre-upgrade backup. The existing restore path is used to confirm the archive can recover the database and application files.

The wrapper does not alter the live database, does not delete older archives and does not claim that a backup is restorable until the manifest and restore checks pass.

| Verification | Result |
|---|---|
| Timestamped archive creation | Passed |
| Manifest verification | Passed |
| Restore after simulated change | Passed |
| Focused regression | Passed |

The focused regression test is `test_upgrade_backup.py`.
