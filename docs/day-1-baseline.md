# Day 1 Baseline Record

**Roadmap day:** 1 — Freeze current MVP baseline  
**Date:** 2026-08-16  
**Repository:** `akameredon/print-recovery-mvp`

## Baseline scope

The current MVP is a local Flask application with a browser operator dashboard. It creates job manifests, hashes source files, records printer/RIP and media metadata, stores logical checkpoints, appends interruption events, produces confidence-aware recovery recommendations and generates an assisted continuation image with configurable overlap.

## Verification evidence

The saved smoke test created a sample image job, recorded a transmitted checkpoint at 150 mm, simulated a power/protection interruption, received a low-confidence `TEST_FIRST` recommendation and generated a non-empty continuation image. The dashboard was opened and visually checked.

## Known limitations

This baseline is generated and locally smoke-tested, not printer-validated. It does not read a real RIP protocol, determine exact physical ink position after a hard trip, control printer movement, guarantee visual seam quality or provide universal printer/RIP compatibility.

## Baseline rule

Future changes must be compared against this baseline. A feature is not considered complete merely because code exists; it must have acceptance evidence appropriate to its roadmap label. Runtime databases, local output files and smoke-test artifacts remain ignored by Git.
