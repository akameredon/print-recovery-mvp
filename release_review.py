from __future__ import annotations

import json
from pathlib import Path


def run_release_review(root: Path) -> dict:
    root = root.resolve()
    required = [
        "app.py",
        "migrations.py",
        "backup_restore.py",
        "secrets_store.py",
        "crash_report.py",
    ]
    checks = {item: (root / item).exists() for item in required}
    checks["workspace_isolation"] = "workspace_id" in (root / "app.py").read_text(encoding="utf-8")
    checks["secret_store"] = (root / "secrets_store.py").exists()
    checks["diagnostics"] = "/healthz" in (root / "app.py").read_text(encoding="utf-8")
    return {
        "review_type": "security_reliability_release_review",
        "status": "ready_for_signoff" if all(checks.values()) else "blocked",
        "checks": checks,
        "limitations": "Automated review is evidence for human sign-off; it is not a penetration test or printer-validation result.",
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    print(json.dumps(run_release_review(parser.parse_args().root), sort_keys=True))


if __name__ == "__main__":
    main()
