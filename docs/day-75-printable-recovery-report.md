# Day 75 — Printable recovery report

**Status:** Implemented and verified.

Day 75 adds `format=print` to the existing recovery-report endpoint. The response is a self-contained print-friendly HTML document with a browser **Print or save as PDF** control, canonical recovery evidence, readiness, source-integrity state, checkpoint, interruption, operator review and safety warnings.

The dashboard exposes **Print or save recovery report** on each job card. The report remains evidence-only: it does not certify physical printer position, print quality or safe continuation without operator review.

| Verification | Result |
|---|---|
| Printable HTML endpoint | Passed |
| Print control and safety boundary | Passed |
| Download filename header | Passed |
| Invalid format handling | Passed |
| Dashboard link | Passed |

The focused test is `test_printable_recovery_report.py`.
