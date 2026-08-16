# Day 20 — Backup and restore command

## Purpose

Day 20 adds a software-only backup and restore command for the local Job Recovery Assistant. It protects the SQLite database, uploaded source files and generated continuation outputs without requiring external storage hardware.

## Commands

Create a backup archive from an application root:

```bash
python3 backup_restore.py backup \
  --root /path/to/print-recovery-mvp \
  --output /path/to/print-recovery-backup.zip
```

Restore a verified archive into an application root:

```bash
python3 backup_restore.py restore \
  --root /path/to/print-recovery-mvp \
  --archive /path/to/print-recovery-backup.zip
```

## Safety behavior

Each archive contains a JSON manifest with the backup format, schema version, relative file paths, sizes and SHA-256 hashes. Restore validates the manifest before extraction, rejects unsupported formats and schema versions, blocks absolute or parent-directory paths, stages files in a temporary directory, verifies every checksum and only then copies files into the target root.

The archive restores the database to `data/print_recovery.sqlite3`, source files under `data/` and generated outputs under `outputs/`. The command is local and does not claim cloud backup, encryption or off-site disaster recovery.

## Verification

The focused test creates a representative application state, creates and restores an archive, verifies byte-for-byte restoration, rejects a tampered member through checksum validation and rejects a path-traversal manifest:

```bash
python3 test_backup_restore.py
```

Day 20 is therefore verified for local archive creation and restoration. Operational backup scheduling, encryption and external storage remain future work.
