# Day 81 — Database integrity checks

**Status:** Implemented and verified.

Day 81 adds database integrity checks to the service health and diagnostics surfaces. SQLite `quick_check`, `integrity_check` and `foreign_key_check` are executed against the active database connection. A healthy result requires `quick_check` and `integrity_check` to return `ok` and no foreign-key violations to be present.

The results are included in `/healthz` and `/api/diagnostics` under `checks.database.integrity`. The dedicated `/api/diagnostics/database-integrity` endpoint returns the same structured result and responds with HTTP 503 when integrity is degraded, making a detected problem visible to monitoring and operators.

A degraded result explicitly advises stopping recovery writes and inspecting diagnostics. This check does not repair a damaged database, restore deleted data or certify that backups are restorable; recovery remains a separate backup-and-restore operation.

| Verification | Result |
|---|---|
| SQLite quick check | Passed |
| SQLite integrity check | Passed |
| Foreign-key check | Passed; no violations |
| Health endpoint propagation | Passed |
| Dedicated integrity endpoint | Passed |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 69 tests |

The focused regression test is `test_database_integrity.py`.
