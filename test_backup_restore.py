import json
import tempfile
import zipfile
from pathlib import Path

from backup_restore import backup, restore

with tempfile.TemporaryDirectory() as workspace:
    root = Path(workspace) / "live"
    restored_root = Path(workspace) / "restored"
    archive = Path(workspace) / "print-recovery-backup.zip"
    (root / "data").mkdir(parents=True)
    (root / "outputs").mkdir(parents=True)
    (root / "data" / "print_recovery.sqlite3").write_bytes(b"database-v1")
    (root / "data" / "job_source.png").write_bytes(b"source-v1")
    (root / "outputs" / "continuation.png").write_bytes(b"output-v1")

    created = backup(root, archive)
    assert created["files"] == 3
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["format"] == "print-recovery-backup"
        assert manifest["schema_version"] == 1
        assert len(manifest["files"]) == 3

    restored = restore(restored_root, archive)
    assert restored["files"] == 3
    for relative_path in (
        "data/print_recovery.sqlite3",
        "data/job_source.png",
        "outputs/continuation.png",
    ):
        assert (restored_root / relative_path).read_bytes() == (root / relative_path).read_bytes()

    tampered = Path(workspace) / "tampered.zip"
    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(tampered, "w") as changed:
        for info in original.infolist():
            content = original.read(info.filename)
            if info.filename == "data/job_source.png":
                content = b"tampered"
            changed.writestr(info, content)
    try:
        restore(Path(workspace) / "tampered-restore", tampered)
    except ValueError as error:
        assert "checksum verification failed" in str(error)
    else:
        raise AssertionError("tampered archive was accepted")

    unsafe = Path(workspace) / "unsafe.zip"
    manifest = {
        "format": "print-recovery-backup",
        "schema_version": 1,
        "files": [{"path": "../escape.txt", "size": 1, "sha256": "0" * 64}],
    }
    with zipfile.ZipFile(unsafe, "w") as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest))
        bundle.writestr("../escape.txt", b"x")
    try:
        restore(Path(workspace) / "unsafe-restore", unsafe)
    except ValueError as error:
        assert "unsafe archive path" in str(error)
    else:
        raise AssertionError("unsafe archive was accepted")

print(
    {"status": "passed", "backup_files": 3, "tamper_rejected": True, "unsafe_path_rejected": True}
)
