from pathlib import Path

ROOT = Path(__file__).resolve().parent
packaging = ROOT / "packaging" / "windows"
plan = (packaging / "service-and-tray-packaging-plan.md").read_text(encoding="utf-8")
launcher = (packaging / "start-print-recovery.ps1").read_text(encoding="utf-8")
validator = (packaging / "validate-package.ps1").read_text(encoding="utf-8")
installer = (packaging / "install-print-recovery.ps1").read_text(encoding="utf-8")
assert "per-machine local service" in plan
assert "tray companion" in plan
assert "does not add automatic printer movement" in plan
assert "healthz" in plan
assert 'PRINT_RECOVERY_HOST = "127.0.0.1"' in launcher
assert "PRINT_RECOVERY_MASTER_KEY" not in launcher
assert "service" not in validator.lower() or "No service registration" in validator
assert "No service registration or data mutation was performed" in validator
assert "Start-Process" not in validator
assert "ProgramData" in installer
assert "Data and encrypted keys" in installer
assert "PRINT_RECOVERY_MASTER_KEY" not in installer
assert "install-manifest.json" in installer
assert (ROOT / "app.py").exists()
assert (ROOT / "requirements.txt").exists()
print(
    {
        "status": "passed",
        "service_plan": True,
        "tray_plan": True,
        "local_only_launcher": True,
        "read_only_preflight": True,
    }
)
