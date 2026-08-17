from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lifecycle_observer import observe_lifecycle


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def archive_trace(
    observed: dict[str, Any], archive_path: Path, *, source: str = "generic_rip_observer"
) -> dict[str, Any]:
    events = list(observed.get("events", []))
    observation = observe_lifecycle(events)
    archive = {
        "archive_schema": "print-recovery.observer-trace/v1",
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "events": events,
        "observation": observation,
    }
    digest = hashlib.sha256(canonical_json(archive).encode("utf-8")).hexdigest()
    archive["archive_sha256"] = digest
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(json.dumps(archive, indent=2) + "\n", encoding="utf-8")
    return archive


def replay_archive(archive_path: Path) -> dict[str, Any]:
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    stored_hash = archive.get("archive_sha256")
    unsigned = {key: value for key, value in archive.items() if key != "archive_sha256"}
    actual_hash = hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()
    replayed = observe_lifecycle(list(archive.get("events", [])))
    return {
        "archive_path": str(archive_path),
        "hash_verified": actual_hash == stored_hash,
        "stored_hash": stored_hash,
        "actual_hash": actual_hash,
        "replay_matches": replayed == archive.get("observation"),
        "replayed_observation": replayed,
    }
