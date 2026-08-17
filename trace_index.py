from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trace_archive import replay_archive


def index_archives(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for archive_path in sorted(root.rglob("*.json")):
        try:
            archive = json.loads(archive_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if archive.get("archive_schema") != "print-recovery.observer-trace/v1":
            continue
        replay = replay_archive(archive_path)
        entries.append(
            {
                "path": str(archive_path),
                "source": archive.get("source"),
                "archived_at": archive.get("archived_at"),
                "archive_sha256": archive.get("archive_sha256"),
                "hash_verified": replay["hash_verified"],
                "replay_matches": replay["replay_matches"],
                "final_state": archive.get("observation", {}).get("final_state"),
                "event_count": len(archive.get("events", [])),
            }
        )
    return sorted(entries, key=lambda entry: (entry.get("archived_at") or "", entry["path"]))


def retrieve_archives(
    root: Path,
    *,
    source: str | None = None,
    final_state: str | None = None,
    verified_only: bool = False,
) -> list[dict[str, Any]]:
    entries = index_archives(root)
    if source is not None:
        entries = [entry for entry in entries if entry["source"] == source]
    if final_state is not None:
        entries = [entry for entry in entries if entry["final_state"] == final_state]
    if verified_only:
        entries = [entry for entry in entries if entry["hash_verified"] and entry["replay_matches"]]
    return entries
