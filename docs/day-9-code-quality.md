# Day 9 — Automated Code Quality Checks

**Roadmap day:** 9  
**Status:** Generated and locally verified  
**Date:** 2026-08-16

## Added

The project now uses Black for consistent Python formatting and Ruff for static analysis and import checks. Standards are defined in `pyproject.toml`, and `requirements-dev.txt` records the development tools needed locally.

The GitHub Actions workflow installs Black and Ruff, checks formatting, runs static analysis, compiles the Python sources and then runs the existing unit, HTTP and recovery tests. Formatting and linting run before the functional tests so quality failures are visible early.

## Verification evidence

Black reported that all 11 checked Python files were correctly formatted. Ruff completed with no findings. Syntax compilation passed, and the complete regression suite passed for models, migrations, configuration, logging, diagnostics, error handling and end-to-end recovery.

## Limitation

The current quality gate covers Python source only. Future work can add HTML/template checks, dependency vulnerability scanning, coverage thresholds and type checking as the application grows.
