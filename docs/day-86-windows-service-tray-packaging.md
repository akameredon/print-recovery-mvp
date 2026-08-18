# Day 86 — Windows service or tray-app packaging plan

**Status:** Implemented and verified as a packaging plan.

Day 86 documents the recommended Windows deployment shape: a per-machine local service should own the Flask process, while an optional tray companion should provide health visibility and dashboard shortcuts without owning the database or bypassing authentication. The service remains bound to loopback by default and does not control a printer or RIP.

The repository now includes `packaging/windows/start-print-recovery.ps1`, which validates the project path, creates local data/output directories, applies loopback launch defaults and starts the existing application. `packaging/windows/validate-package.ps1` performs a read-only preflight for Python and required project files. Neither script registers a service, elevates privileges or deletes data.

The plan defines the later installer requirements for a pinned and checksummed service wrapper, dedicated non-administrator service account, protected secret configuration, health-gated installation, upgrade preservation of the database and encrypted key, and rollback behavior. It deliberately does not claim that a production installer or tray executable has been built.

| Verification | Result |
|---|---|
| Packaging plan content | Passed |
| Loopback-only launch defaults | Passed |
| Secret exclusion from launcher | Passed |
| Read-only preflight contract | Passed |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 74 tests |
| PowerShell runtime syntax validation | Not available in the Linux verification environment; static script checks passed |

The focused regression test is `test_windows_packaging_plan.py`.
