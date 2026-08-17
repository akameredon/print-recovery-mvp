# Day 60 — Recovery Readiness Dashboard

**Status:** Implemented and verified  
**Roadmap day:** 60  
**Scope:** Operator-facing readiness summaries for assisted recovery

## Delivered

Day 60 adds a compact readiness-summary contract and dashboard panel. The existing detailed `/api/jobs/<job_id>/readiness` response remains the source of truth for integrity, checkpoint, interruption and recovery-safety evidence. The new `/api/jobs/<job_id>/readiness-summary` endpoint transforms that evidence into operator-facing blockers, warnings and next actions.

The dashboard now exposes a **Show readiness summary** control on every job card. The panel distinguishes blocked recovery from operator review, lists the evidence issues that must be addressed, and states whether continuation generation is safe under the current evidence. It keeps the safety boundary explicit: operator confirmation remains required, and a positive summary does not certify the physical printer position.

## Readiness behavior

| State | Dashboard behavior | Operator implication |
|---|---|---|
| `blocked` | Red-tinted panel with blockers and corrective actions | Do not generate a continuation until every blocker is resolved. |
| `review_required` | Review panel with warnings and test-first guidance | Inspect evidence and use a registration test before continuation. |
| `ready_for_operator_review` | Review panel with approval guidance | Review the evidence bundle and record explicit approval or rejection. |

The summary intentionally reports `operator_confirmation_required: true` for every state. The `safe_to_generate` field means that the evidence gate is satisfied, not that the software has verified exact physical printer alignment.

## Verification evidence

The focused `test_readiness_summary.py` script passed all three readiness states and checked the dashboard endpoint, JavaScript control and panel markup. Static checks also passed: Black reported all files unchanged, Ruff reported no errors, and Python compilation succeeded for the modified modules.

The complete non-restart regression suite passed against a healthy local Flask service. The checkpoint durability test was run separately with its intended process-restart lifecycle and passed with the checkpoint and event preserved across restart. The repository’s existing API, recovery, evidence, observer, trace, dashboard and usability tests remained passing.

## Status boundary

This milestone improves operator visibility and decision discipline. It does not add printer control, universal RIP compatibility or physical-position measurement. Those limitations remain intentionally visible in the dashboard and documentation.
