# Day 4 — Database Migration and Version Tracking

**Roadmap day:** 4  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now uses a versioned SQLite migration runner. A `schema_migrations` table records each applied migration, its version, name and application time. Migration 1 creates the initial jobs, checkpoints, events and decisions schema. Migration 2 adds operational indexes for job updates, checkpoint lookup, event lookup and decision lookup.

The migration runner executes during application startup, applies only missing versions and safely does nothing on later startups when the schema is current. Existing databases created by the earlier MVP are supported because the initial migration uses idempotent `CREATE TABLE IF NOT EXISTS` statements and the index migration uses `CREATE INDEX IF NOT EXISTS`.

## Verification evidence

The migration test passed on a fresh temporary database, confirmed versions 1 and 2, confirmed that a second run was idempotent, verified the required tables and verified the operational job index. The full configuration, logging and recovery smoke tests also passed after restarting the application with the migration runner.

## Limitation

The current migration set is intentionally small. Future changes must add a new numbered migration rather than editing an already-applied migration. Production upgrades should later add backup-before-migration and rollback procedures.
