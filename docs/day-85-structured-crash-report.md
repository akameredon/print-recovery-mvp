# Day 85 — Structured crash-report export

**Status:** Implemented and verified.

Day 85 adds an authenticated structured crash-report export at `/api/diagnostics/crash-report`. Technicians and owners can export a JSON report containing a report identifier, service version, timestamp, selected diagnostic checks, safe configuration fields, recent error records and explicit limitations.

The exporter does not return raw logs. It redacts sensitive key names such as passwords, secrets, tokens, API keys, private keys, authorization values and cookies. Path-related values are reduced to basenames, and bearer-token patterns are redacted. The response is marked as a downloadable `print_recovery_crash_report.json` attachment and is unavailable to operators.

The report is intended for structured troubleshooting and support handoff. It does not establish physical printer state, print quality or continuation safety, and it does not replace the secret-safe technician support bundle from Day 80.

| Verification | Result |
|---|---|
| Structured JSON export | Passed |
| Secret and token redaction | Passed |
| Path reduction | Passed |
| Owner/technician access control | Passed |
| Download header | Passed |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 73 tests |

The focused regression test is `test_crash_report_export.py`.
