# Day 8 — Continuous Integration Smoke Tests

**Roadmap day:** 8  
**Status:** Generated and locally verified  
**Date:** 2026-08-16

## Added

The repository now includes `.github/workflows/ci.yml`. GitHub Actions runs on pushes to `master` and on pull requests targeting `master`. The workflow checks out the repository, sets up Python 3.11, installs `requirements.txt`, compiles the Python sources, runs isolated migration/configuration/model tests, starts the application and runs logging, diagnostics, error-handling and end-to-end recovery tests.

If a workflow run fails, the application logs are uploaded as an artifact when available. The workflow has read-only contents permission.

## Verification evidence

The workflow structure was checked locally for required actions and test commands. The same compile, unit, HTTP and recovery commands used by CI passed locally.

## Limitation

The workflow has not yet been confirmed by a completed remote GitHub Actions run in this document. After pushing, inspect the Actions tab for the first hosted run. Later improvements can add coverage reporting, dependency vulnerability checks, matrix testing and release gates.
