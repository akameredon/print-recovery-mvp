# Print Recovery MVP Installation Guide

**Roadmap day:** 10  
**Status:** Generated and locally verified  
**Date:** 2026-08-16

## Scope

This guide installs the current local MVP for development and controlled testing. It does not install printer drivers, connect to a production RIP, control printer hardware or certify recovery accuracy.

## Prerequisites

| Requirement | Minimum or supported value |
|---|---|
| Python | 3.11 or newer |
| Git | Required to clone the repository |
| Operating system | Windows, macOS or Linux with Python and a terminal |
| Browser | A current Chromium, Firefox or Safari browser |
| Storage | Enough space for source files, logs and test outputs |

## Install from GitHub

```bash
git clone https://github.com/akameredon/print-recovery-mvp.git
cd print-recovery-mvp
python3 -m venv .venv
```

Activate the virtual environment:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install development dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

The development requirements include the runtime dependencies plus Black and Ruff. For a runtime-only installation, use `pip install -r requirements.txt` instead.

## Configure

Copy `config.example.json` to `config.json` if local overrides are needed. The application also accepts environment variables such as `PRINT_RECOVERY_PORT`, `PRINT_RECOVERY_LOG_LEVEL`, `PRINT_RECOVERY_DATA_DIR`, `PRINT_RECOVERY_OUTPUT_DIR` and `PRINT_RECOVERY_MAX_UPLOAD_MB`.

Do not put passwords, API keys or printer credentials in `config.json`. Runtime data and the local database are intentionally ignored by Git.

## Verify the installation

Run the quality checks and regression suite:

```bash
black --check app.py config.py logging_utils.py migrations.py test_*.py
ruff check app.py config.py logging_utils.py migrations.py test_*.py
python -m py_compile app.py config.py logging_utils.py migrations.py
python test_models.py
python test_migrations.py
python test_config.py
python test_logging.py
python test_diagnostics.py
python test_error_handling.py
python test_mvp.py
```

A successful installation reports passing results for the isolated database tests, configuration tests, structured logging, diagnostics, error handling and end-to-end recovery smoke workflow.

## Start the application

```bash
python app.py
```

Open `http://127.0.0.1:5173` in a browser. The health endpoint is available at `http://127.0.0.1:5173/healthz`, and detailed diagnostics are available at `http://127.0.0.1:5173/api/diagnostics`.

Stop the application with `Ctrl+C` in the terminal. The local SQLite database is created under `data/`, and application logs are written to `data/print_recovery.log`.

## Clean-machine verification

To verify a clean installation, use a new directory or machine, clone the repository again, create a new virtual environment, install `requirements-dev.txt`, run the full test commands, start the application and confirm that `/healthz` returns HTTP 200 with schema versions `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]`. Do not copy an existing `data/` directory into the test because that would hide migration and first-start problems.

## Troubleshooting

| Symptom | Action |
|---|---|
| `python` is not found | Install Python 3.11+ and ensure it is on PATH |
| Port 5173 is busy | Set `PRINT_RECOVERY_PORT` to another free port |
| Browser cannot connect | Confirm the terminal shows the server started and use the configured host/port |
| Health returns 503 | Open `/api/diagnostics` and inspect database, migration and path checks |
| Dependency installation fails | Upgrade pip, confirm network access and retry in a fresh virtual environment |
| Tests cannot find the application | Run commands from the repository root with the virtual environment activated |
| Printer integration is expected | This MVP is not yet printer-integrated; provide the exact printer and RIP details before adding an adapter |

## Status boundary

This guide proves reproducible installation of the current software prototype. It does not prove production readiness, multi-user deployment, universal printer compatibility or accurate physical continuation after a real power trip.
