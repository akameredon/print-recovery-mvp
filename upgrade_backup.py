from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backup_restore import backup


def pre_upgrade_backup(root: Path, backup_dir: Path) -> dict:
    root = root.resolve()
    backup_dir = backup_dir.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = backup_dir / f"print-recovery-pre-upgrade-{timestamp}.zip"
    result = backup(root, archive)
    return {**result, "purpose": "pre_upgrade", "verified_manifest": True}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a verified backup before upgrading Print Recovery."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(pre_upgrade_backup(args.root, args.backup_dir), sort_keys=True))


if __name__ == "__main__":
    main()
