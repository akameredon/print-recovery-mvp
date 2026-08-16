# Day 6 — Consistent Error Handling

**Roadmap day:** 6  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now returns a consistent JSON error object for API and JSON requests. The object contains an error code, human-readable message, HTTP status and correlation ID. Common HTTP failures such as 404 and 405 are handled explicitly.

Browser requests receive a simple error page that shows the status, a safe message, a correlation ID and a link back to the dashboard. Unexpected exceptions are logged with stack traces but do not expose internal details to the user; the correlation ID is provided for support.

## Verification evidence

The Day 6 test passed for JSON 404, JSON 405, browser 404 rendering and correlation-ID propagation. The migration, configuration, logging, diagnostics and full recovery smoke tests also passed.

## Limitation

The current error catalogue is small and localised to the MVP. Later work should add domain-specific validation errors, translation support and structured support bundles while preserving the same public response contract.
