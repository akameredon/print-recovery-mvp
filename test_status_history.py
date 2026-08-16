import sqlite3
import tempfile

from app import record_status_transition
from migrations import run_migrations

with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
    conn = sqlite3.connect(handle.name)
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    conn.execute(
        "INSERT INTO jobs(id,file_name,source_path,source_hash,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (
            "job-status",
            "sample.png",
            "/tmp/sample.png",
            "hash",
            "READY",
            "2026-01-01",
            "2026-01-01",
        ),
    )
    conn.execute(
        "INSERT INTO job_status_history(job_id,from_status,to_status,reason,source,created_at) VALUES(?,?,?,?,?,?)",
        ("job-status", None, "READY", "job_created", "operator", "2026-01-01"),
    )
    assert record_status_transition(
        conn, "job-status", "PRINTING", "checkpoint_recorded", "adapter"
    )
    assert not record_status_transition(conn, "job-status", "PRINTING", "duplicate", "adapter")
    assert record_status_transition(
        conn, "job-status", "INTERRUPTED", "POWER_OR_PROTECTION_TRIP", "operator"
    )
    conn.commit()
    rows = conn.execute(
        "SELECT from_status,to_status,reason FROM job_status_history WHERE job_id=? ORDER BY id",
        ("job-status",),
    ).fetchall()
    assert [tuple(row) for row in rows] == [
        (None, "READY", "job_created"),
        ("READY", "PRINTING", "checkpoint_recorded"),
        ("PRINTING", "INTERRUPTED", "POWER_OR_PROTECTION_TRIP"),
    ]
    final_status = conn.execute("SELECT status FROM jobs WHERE id=?", ("job-status",)).fetchone()[0]
    assert final_status == "INTERRUPTED"
    conn.close()
print({"status": "passed", "transitions": 3, "duplicate_transition": "suppressed"})
