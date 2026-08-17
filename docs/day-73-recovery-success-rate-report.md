# Day 73 — Recovery success-rate report

**Status:** Implemented and verified  
**Roadmap day:** 73  
**Scope:** Owner-scoped recovery decision outcome reporting

## Delivered

Day 73 adds `GET /api/reports/recovery-success-rate`. The endpoint accepts an optional `week_start=YYYY-MM-DD` query parameter and defaults to the Monday of the current UTC week. It is restricted to owners and filters decisions through the authenticated owner’s active workspace.

The report exposes visible categories for `approved`, `rejected`, `restart`, `pending`, `test_first` and `other` decisions. Its success rate is calculated only from reviewed decisions:

> Success rate = approved decisions ÷ (approved decisions + rejected decisions) × 100.

Pending, restart and test-first outcomes are not silently treated as successes or failures; they remain separately visible so management can distinguish unresolved work from an explicit outcome. When no decisions have been reviewed, the API returns a `null` success rate rather than implying a zero-performance result.

## Dashboard workflow

Owners now have a **Recovery success-rate report** panel on the dashboard. They can select a week, load the report, see the percentage and category counts, and read the measurement boundary. Non-owner users see a permission message and cannot access the report endpoint.

## Safety and measurement boundary

The report summarizes software-recorded recovery decisions. An approved decision means that the recorded review action was approved; it does not prove that the printer physically aligned, that the continuation produced an acceptable print, or that material was actually recovered. Those physical outcomes require operator validation and remain outside the software-only evidence boundary.

## Verification evidence

The focused `test_recovery_success_rate.py` test verifies category classification, the 50% reviewed-decision fixture, Monday-to-Sunday date bounds, invalid-date handling, owner-only access and dashboard markup. During full-suite verification, the fixture was isolated in a dedicated workspace after discovering that the persistent SQLite database correctly retained earlier regression data in the default workspace; this prevented cross-test contamination without weakening production workspace filtering.

The final checks passed:

| Check | Result |
|---|---|
| Black formatting gate | Passed; 71 files unchanged |
| Ruff lint gate | Passed |
| Python compilation | Passed |
| Non-restart regression suite | Passed; 66 tests |
| Focused Day 73 test | Passed |

## Limitations

This milestone does not control a printer or RIP, infer a physical print head position, certify a continuation boundary, or claim universal Mimaki, Roland or other printer compatibility. It improves management visibility into software-recorded decisions while preserving the existing assisted-recovery safeguards.
