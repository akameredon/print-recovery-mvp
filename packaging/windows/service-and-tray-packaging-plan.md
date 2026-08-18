# Day 86 — Windows service or tray-app packaging plan

**Status:** Packaging approach documented and launch scripts verified. No installer is claimed by this milestone.

## Recommended deployment shape

The first Windows deployment should run the existing Flask application as a **per-machine local service** bound to `127.0.0.1`. A service wrapper such as WinSW or NSSM should own the Python process, restart it after an unexpected process exit, redirect standard output and error to the existing structured log location, and run under a dedicated non-administrator Windows service account. The wrapper binary must be pinned, checksummed and included in a later reproducible installer milestone.

A lightweight **tray companion** is an optional operator convenience rather than the process owner. It can open the local dashboard, show service health and provide Start/Stop/Restart controls through the Windows Service Control Manager. It must not duplicate the recovery database, bypass authentication or send printer-control commands.

| Concern | Service process | Tray companion |
|---|---|---|
| Owns the Flask process | Yes | No |
| Runs when no operator is logged in | Yes | No |
| Shows local health and dashboard shortcut | Optional | Yes |
| Requires administrator rights during installation | Usually | No after installation |
| Stores job data independently | No | No |
| Controls a printer or RIP | No | No |

## Installation sequence for a future installer

The installer should create an application directory under `C:\Program Files\PrintRecovery`, a writable data directory under `C:\ProgramData\PrintRecovery`, a dedicated service account, the service wrapper registration, a firewall rule only if a future approved network mode requires it, and an uninstaller that stops the service before removing binaries. It must preserve the database and encrypted key file unless the owner explicitly selects data removal.

The installer must validate Python/runtime dependencies, write a machine-scoped configuration path, set `PRINT_RECOVERY_SESSION_SECRET` and `PRINT_RECOVERY_MASTER_KEY` through protected machine configuration rather than command-line arguments, and verify `/healthz` before reporting success. Secrets must never be placed in the service XML, PowerShell transcript, shortcut target or tray logs.

## Launch scripts delivered in Day 86

`start-print-recovery.ps1` validates the project path and Python executable, applies local-only defaults, and launches `app.py`. `validate-package.ps1` performs a read-only preflight for Python, required source files, the configured data/output directories and the migration module. These scripts are intentionally not installers and do not elevate privileges or register a service.

## Operational safety boundary

This plan packages the existing **software-only, assisted-recovery** workflow. It does not add automatic printer movement, RIP control, universal device support, physical-position measurement or a production installer. Service restart behavior improves availability of local capture; it does not prove that a printer physically resumed at an exact coordinate.

## Acceptance checklist for a later installer milestone

| Check | Required evidence |
|---|---|
| Clean Windows machine | Installation completes without developer tools |
| Service lifecycle | Start, stop, restart and unexpected-exit recovery pass |
| Local-only binding | Service listens on loopback unless explicitly configured |
| Data preservation | Upgrade/uninstall does not silently delete database or encrypted key |
| Secret handling | No secrets in command lines, XML, transcripts or logs |
| Health gate | Installer verifies `/healthz` before success |
| Rollback | Failed upgrade restores the previous service binary and configuration |
