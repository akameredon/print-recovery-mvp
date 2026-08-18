# Print Recovery State Capture MVP

This is the first local prototype of the software-first recovery assistant. It currently provides a protected job manifest, source hashing, logical checkpoint recording, interruption events, confidence-aware recovery recommendations and assisted continuation generation for image test jobs.

## Run (development)

From this directory:

```bash
python3 app.py
```

Open `http://127.0.0.1:5173` in a browser. Create a test job with an image and media dimensions, record one or more checkpoints, mark an interruption, review the recommendation and generate a continuation image.

## Windows desktop / installer

To produce a normal Windows program (`.exe` + Next → Next → Finish installer) that you can put on a flash drive, see:

**[docs/desktop-packaging.md](docs/desktop-packaging.md)**

Key files already in the repo:

- `packaging/windows/build-exe.ps1` — builds the standalone `PrintRecovery.exe`
- `packaging/windows/PrintRecovery.iss` — Inno Setup script for the real installer
- `packaging/windows/create-portable.ps1` — makes a flash-drive ready folder
- `packaging/windows/Run-PrintRecovery.bat` — simple double-click launcher

## Installation (source)

See [docs/installation.md](docs/installation.md) for prerequisites, setup, configuration, testing, startup and troubleshooting.

## Roadmap

See [docs/100-day-roadmap.md](docs/100-day-roadmap.md) for the one-improvement-per-day plan from MVP toward a multi-user beta.

## Current status

The prototype is **generated but not printer-validated**. It does not read a real RIP protocol, control a printer, prove physical ink position or guarantee continuation quality. It is intentionally safe and local: no printer-control commands are sent.

## Next integration

Select one exact printer model and RIP workflow. Add an adapter that can observe the actual job or queue events, then compare host-side checkpoints with measured media position during controlled tests.
