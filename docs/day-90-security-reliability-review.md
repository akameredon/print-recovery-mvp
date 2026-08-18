# Day 90 — Security and reliability release review

**Status:** Automated review implemented and verified; human release sign-off remains required.

Day 90 adds `release_review.py`, a reproducible checklist that verifies the presence of database migration, backup/restore, encrypted-secret, crash-diagnostics and workspace-isolation controls. It reports `ready_for_signoff` only when all checks pass.

The report is evidence for a human security and reliability review. It is not a penetration test, an independent security audit, a clean-machine installer result or printer/RIP validation.

The focused regression test is `test_release_review.py`.
