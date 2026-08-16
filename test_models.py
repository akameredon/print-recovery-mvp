import json
import sqlite3
import tempfile

from migrations import run_migrations

with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
    conn = sqlite3.connect(handle.name)
    run_migrations(conn)

    conn.execute(
        "INSERT INTO jobs(id,file_name,source_path,source_hash,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (
            "job-unit",
            "sample.png",
            "/tmp/sample.png",
            "abc123",
            "READY",
            "2026-01-01",
            "2026-01-01",
        ),
    )
    job = conn.execute("SELECT id,file_name,status FROM jobs WHERE id=?", ("job-unit",)).fetchone()
    assert job == ("job-unit", "sample.png", "READY")

    conn.execute(
        "INSERT INTO checkpoints(job_id,y_mm,band_mm,state,evidence,confidence,created_at) VALUES(?,?,?,?,?,?,?)",
        ("job-unit", 150.0, 5.0, "PRINTING", "transmitted", "transmitted", "2026-01-01"),
    )
    checkpoint = conn.execute(
        "SELECT y_mm,evidence,confidence FROM checkpoints WHERE job_id=?", ("job-unit",)
    ).fetchone()
    assert checkpoint == (150.0, "transmitted", "transmitted")

    payload = {"event": "POWER_OR_PROTECTION_TRIP", "note": "unit test"}
    conn.execute(
        "INSERT INTO events(job_id,event_type,source,payload,created_at) VALUES(?,?,?,?,?)",
        ("job-unit", "POWER_OR_PROTECTION_TRIP", "operator", json.dumps(payload), "2026-01-01"),
    )
    event_payload = json.loads(
        conn.execute("SELECT payload FROM events WHERE job_id=?", ("job-unit",)).fetchone()[0]
    )
    assert event_payload == payload

    conn.execute(
        "INSERT INTO decisions(job_id,selected_y_mm,overlap_mm,mode,recommendation,confidence,operator_action,created_at) VALUES(?,?,?,?,?,?,?,?)",
        ("job-unit", 150.0, 5.0, "assisted", "TEST_FIRST", "low", "approved", "2026-01-01"),
    )
    decision = conn.execute(
        "SELECT recommendation,mode,operator_action FROM decisions WHERE job_id=?", ("job-unit",)
    ).fetchone()
    assert decision == ("TEST_FIRST", "assisted", "approved")

    conn.commit()
    conn.close()
print({"status": "passed", "models": ["jobs", "checkpoints", "events", "decisions"]})
