# Day 11 — Job Status History

**Roadmap day:** 11  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now records an append-only status history for each job in `job_status_history`. Every recorded transition stores the previous status, new status, reason, source and timestamp. The current job status remains on the `jobs` table for fast lookup, while the history provides an audit trail.

The current lifecycle records `READY` when a job is created, `PRINTING` when a checkpoint is recorded, `INTERRUPTED` when a trip or interruption is reported and `RECOVERY_READY` when a continuation file is generated. Duplicate transitions are suppressed unless explicitly forced. The job-detail endpoint now returns `status_history` in chronological order.

Migration 3 creates the status-history table and its job lookup index. Existing databases are upgraded automatically by the migration runner.

## Verification evidence

The status-history test passed for ordered transitions, duplicate-transition suppression and final job status. The migration test passed with versions `[1, 2, 3]` and confirmed idempotence plus the new table and index. Configuration, logging, diagnostics, error-handling and end-to-end recovery tests also passed after restarting the application.

## Limitation

The history records software-observed lifecycle transitions. It does not prove that a printer physically reached the corresponding position or that a status change was acknowledged by a real printer protocol. That evidence remains part of future adapter-specific work.
