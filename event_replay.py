from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


def replay_timeline(db_path: Path, job_id: str) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if not conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone():
        conn.close()
        raise ValueError("JOB_NOT_FOUND")
    items: list[dict[str, Any]] = []
    for row in conn.execute(
        "SELECT * FROM job_status_history WHERE job_id=?", (job_id,)
    ).fetchall():
        items.append(
            {
                "id": row["id"],
                "kind": "status_transition",
                "timestamp": row["created_at"],
                "source": row["source"],
                "event": row["to_status"],
                "details": {
                    "from_status": row["from_status"],
                    "reason": row["reason"],
                },
            }
        )
    for row in conn.execute("SELECT * FROM checkpoints WHERE job_id=?", (job_id,)).fetchall():
        items.append(
            {
                "id": row["id"],
                "kind": "checkpoint",
                "timestamp": row["created_at"],
                "source": "checkpoint_recorder",
                "event": "CHECKPOINT",
                "details": {
                    key: row[key] for key in row.keys() if key not in {"id", "job_id", "created_at"}
                },
            }
        )
    for row in conn.execute("SELECT * FROM events WHERE job_id=?", (job_id,)).fetchall():
        items.append(
            {
                "id": row["id"],
                "kind": "event",
                "timestamp": row["created_at"],
                "source": row["source"],
                "event": row["event_type"],
                "payload_raw": row["payload"],
            }
        )
    for row in conn.execute("SELECT * FROM decisions WHERE job_id=?", (job_id,)).fetchall():
        items.append(
            {
                "id": row["id"],
                "kind": "decision",
                "timestamp": row["created_at"],
                "source": "recovery_assistant",
                "event": row["recommendation"],
                "details": {
                    key: row[key] for key in row.keys() if key not in {"id", "job_id", "created_at"}
                },
            }
        )
    conn.close()
    items.sort(key=lambda item: (item["timestamp"], item["kind"], item["id"]))
    return {"job_id": job_id, "total": len(items), "items": items}


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a recorded print-recovery timeline")
    parser.add_argument("--db", default="data/print_recovery.sqlite3")
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    try:
        result = replay_timeline(Path(args.db), args.job_id)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
