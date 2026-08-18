# Day 87 — Reproducible Windows installer artifact

**Status:** Script artifact implemented; Windows execution remains to be verified on a clean Windows machine.

Day 87 adds `packaging/windows/install-print-recovery.ps1`, a launch-only installer script that creates a local Python virtual environment, installs the pinned project requirements, copies application files, generates a launch script and writes an SHA-256 install manifest. It preserves the separate `ProgramData` data directory and encrypted key material during uninstall.

The script does not register a Windows service, set secrets on the command line, delete application data during uninstall, or claim a clean-machine installation test in this Linux environment. Those items remain acceptance checks for a Windows-hosted packaging run.
