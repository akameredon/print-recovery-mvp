import sqlite3
import tempfile

from migrations import applied_versions, run_migrations

with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
    conn = sqlite3.connect(handle.name)
    first = run_migrations(conn)
    assert [version for version, _ in first] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert applied_versions(conn) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    second = run_migrations(conn)
    assert second == []
    assert applied_versions(conn) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {
        "schema_migrations",
        "jobs",
        "checkpoints",
        "events",
        "decisions",
        "job_status_history",
        "users",
        "audit_log",
    }.issubset(tables)
    indexes = {row[1] for row in conn.execute("PRAGMA index_list('jobs')")}
    assert "idx_jobs_updated_at" in indexes
    status_indexes = {row[1] for row in conn.execute("PRAGMA index_list('job_status_history')")}
    assert "idx_status_history_job_id" in status_indexes
    checkpoint_columns = {row[1] for row in conn.execute("PRAGMA table_info(checkpoints)")}
    assert {"logical_band", "pass_number"}.issubset(checkpoint_columns)
    job_columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    assert {"overlap_mm", "orientation"}.issubset(job_columns)
    user_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    assert {"password_hash", "last_login_at"}.issubset(user_columns)
    audit_columns = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)")}
    assert {"actor_user_id", "action", "resource_type", "details"}.issubset(audit_columns)

    conn.close()
print({"status": "passed", "versions": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "second_run": "idempotent"})
