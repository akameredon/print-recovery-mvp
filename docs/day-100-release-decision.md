# Day 100 — Evidence-based release decision

**Status:** Decision workflow implemented and verified. No release decision is being fabricated without field evidence.

Day 100 adds an owner-only `POST /api/release-decision` endpoint and a technician/owner `GET /api/release-decision` endpoint. The decision must be `release`, `extend_pilot` or `return_to_engineering`, must reference an exactly seven-day pilot window, and must include a rationale and evidence object. Every decision is recorded in the existing audit log.

A `release` decision is rejected unless the evidence states `field_validation_status=field_validated`, includes at least one physical test and confirms that support review is complete. If those conditions are absent, the API returns HTTP 409 with `RELEASE_EVIDENCE_INSUFFICIENT` and recommends extending the pilot. This prevents software-only records from being presented as printer-specific validation.

`extend_pilot` and `return_to_engineering` decisions can be recorded with a documented rationale and software evidence. The response clearly states that governance evidence does not guarantee printer-specific recovery accuracy.

| Verification | Result |
|---|---|
| Release evidence gate | Passed |
| Insufficient-evidence rejection | Passed |
| Extend-pilot recording | Passed |
| Latest decision retrieval | Passed |
| Owner-only write access | Implemented |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 80 tests |

The focused regression test is `test_release_decision.py`.

> Final roadmap distinction: the product now has a controlled decision mechanism, but the mechanism cannot manufacture a go/no-go result. A real release decision still requires dated evidence from a named shop, target printer/RIP and physical validation.
