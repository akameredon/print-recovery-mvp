import sqlite3
import tempfile

from migrations import applied_versions, run_migrations

with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
    conn = sqlite3.connect(handle.name)
    first = run_migrations(conn)
    assert [version for version, _ in first] == [1, 2, 3]
    assert applied_versions(conn) == [1, 2, 3]
    second = run_migrations(conn)
    assert second == []
    assert applied_versions(conn) == [1, 2, 3]
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {
        "schema_migrations",
        "jobs",
        "checkpoints",
        "events",
        "decisions",
        "job_status_history",
    }.issubset(tables)
    indexes = {row[1] for row in conn.execute("PRAGMA index_list('jobs')")}
    assert "idx_jobs_updated_at" in indexes
    status_indexes = {row[1] for row in conn.execute("PRAGMA index_list('job_status_history')")}
    assert "idx_status_history_job_id" in status_indexes

    conn.close()
print({"status": "passed", "versions": [1, 2, 3], "second_run": "idempotent"})
