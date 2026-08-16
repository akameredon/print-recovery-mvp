# Day 3 — Local Configuration File

**Roadmap day:** 3  
**Status:** Generated and verified  
**Date:** 2026-08-16

## Added

The MVP now loads optional JSON configuration from `config.json` or the path in `PRINT_RECOVERY_CONFIG`. Defaults continue to work without any configuration file. The supported settings are data directory, output directory, log level, host, port and maximum upload size in megabytes.

Each setting can also be overridden with an environment variable: `PRINT_RECOVERY_DATA_DIR`, `PRINT_RECOVERY_OUTPUT_DIR`, `PRINT_RECOVERY_LOG_LEVEL`, `PRINT_RECOVERY_HOST`, `PRINT_RECOVERY_PORT` and `PRINT_RECOVERY_MAX_UPLOAD_MB`. Relative paths resolve from the application root, while absolute paths are accepted.

The example file is `config.example.json`. The configuration loader validates the port range, upload-size value and JSON object shape before application startup.

## Verification evidence

The configuration test passed for defaults, JSON overrides, environment-variable overrides and relative-path resolution. The full MVP smoke test and structured-logging test also passed after restarting the application with the configuration-integrated code.

## Limitation

This is a local configuration layer, not yet a production secrets manager, multi-tenant configuration service or deployment orchestrator. Sensitive credentials must not be placed in the JSON file.
