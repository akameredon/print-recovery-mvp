import tempfile
from pathlib import Path

from backup_restore import restore
from upgrade_backup import pre_upgrade_backup

with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as backups:
    root = Path(workspace)
    (root / "data").mkdir()
    (root / "data" / "print_recovery.sqlite3").write_text("database", encoding="utf-8")
    result = pre_upgrade_backup(root, Path(backups))
    archive = Path(result["archive"])
    assert result["purpose"] == "pre_upgrade"
    assert result["verified_manifest"] is True
    assert archive.exists()
    (root / "data" / "print_recovery.sqlite3").write_text("changed", encoding="utf-8")
    restored = restore(root, archive)
    assert restored["files"] >= 1
    assert (root / "data" / "print_recovery.sqlite3").read_text(encoding="utf-8") == "database"
print({"status": "passed", "pre_upgrade_backup": True, "restore_verified": True})
