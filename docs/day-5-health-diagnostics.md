# Day 5 — Health Checks and Startup Diagnostics

**Roadmap day:** 5  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now exposes `GET /healthz` for a lightweight service-health result and `GET /api/diagnostics` for a more detailed operator or support diagnostic response. Both check database connectivity, applied schema versions, expected migration versions and writable data/output paths.

A healthy response returns HTTP 200. If the database schema is incomplete, a path is unavailable or a diagnostic check fails, the health endpoint returns a degraded response with HTTP 503. The diagnostics response includes safe configuration fields and the current request correlation ID but does not expose source-file paths or job contents.

## Verification evidence

The Day 5 diagnostics test passed with HTTP 200, status `ok`, schema versions `[1, 2]`, writable paths and propagated correlation IDs. The migration, configuration, logging and full recovery smoke tests also passed after restarting the application with the new routes.

## Limitation

The diagnostics are local-process checks only. They do not yet test printer connectivity, RIP availability, disk capacity thresholds, backup freshness or external notification channels. Those checks should be added only when the corresponding integrations exist.
