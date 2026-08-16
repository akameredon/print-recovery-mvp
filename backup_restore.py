#!/usr/bin/env python3
"""Create and restore verified local backups for the print-recovery MVP."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

SCHEMA_VERSION = 1
BACKUP_FORMAT = "print-recovery-backup"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def file_entries(root: Path) -> list[tuple[str, Path]]:
    candidates = []
    database = root / "data" / "print_recovery.sqlite3"
    if database.is_file():
        candidates.append(("data/print_recovery.sqlite3", database))
    for directory_name in ("data", "outputs"):
        directory = root / directory_name
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path != database:
                candidates.append((f"{directory_name}/{path.relative_to(directory)}", path))
    return candidates


def build_manifest(root: Path, entries: list[tuple[str, Path]]) -> dict:
    return {
        "format": BACKUP_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "files": [
            {"path": archive_path, "size": path.stat().st_size, "sha256": digest(path)}
            for archive_path, path in entries
        ],
    }


def backup(root: Path, archive: Path) -> dict:
    root = root.resolve()
    archive = archive.resolve()
    entries = file_entries(root)
    manifest = build_manifest(root, entries)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        for archive_path, source_path in entries:
            bundle.write(source_path, archive_path)
    return {"operation": "backup", "archive": str(archive), "files": len(entries)}


def safe_member_path(root: Path, member: str) -> Path:
    path = Path(member)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe archive path: {member}")
    target = (root / path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"unsafe archive path: {member}")
    return target


def read_and_validate_manifest(bundle: zipfile.ZipFile) -> dict:
    try:
        manifest = json.loads(bundle.read("manifest.json"))
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError("backup manifest is missing or invalid JSON") from exc
    if not isinstance(manifest, dict):
        raise ValueError("backup manifest must be an object")
    if manifest.get("format") != BACKUP_FORMAT:
        raise ValueError("unsupported backup format")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported backup schema version")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("backup manifest files must be a list")
    names = set(bundle.namelist())
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("each manifest file entry must include a path")
        member = entry["path"]
        safe_member_path(Path("/tmp/backup-validation"), member)
        if member not in names:
            raise ValueError(f"manifest file is missing from archive: {member}")
        if not isinstance(entry.get("sha256"), str) or len(entry["sha256"]) != 64:
            raise ValueError(f"invalid SHA-256 for archive member: {member}")
    return manifest


def restore(root: Path, archive: Path) -> dict:
    root = root.resolve()
    archive = archive.resolve()
    if not archive.is_file():
        raise ValueError(f"backup archive does not exist: {archive}")
    with zipfile.ZipFile(archive) as bundle:
        manifest = read_and_validate_manifest(bundle)
        with tempfile.TemporaryDirectory(prefix="print-recovery-restore-") as temporary:
            staging = Path(temporary)
            for entry in manifest["files"]:
                member = entry["path"]
                target = safe_member_path(staging, member)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
                if target.stat().st_size != entry["size"] or digest(target) != entry["sha256"]:
                    raise ValueError(f"checksum verification failed: {member}")
            for entry in manifest["files"]:
                source = staging / entry["path"]
                destination = safe_member_path(root, entry["path"])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
    return {"operation": "restore", "archive": str(archive), "files": len(manifest["files"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    backup_parser = subparsers.add_parser("backup", help="create a verified backup archive")
    backup_parser.add_argument("--root", type=Path, default=Path("."))
    backup_parser.add_argument("--output", type=Path, required=True)
    restore_parser = subparsers.add_parser("restore", help="restore a verified backup archive")
    restore_parser.add_argument("--root", type=Path, default=Path("."))
    restore_parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    result = (
        backup(args.root, args.output)
        if args.command == "backup"
        else restore(args.root, args.archive)
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
