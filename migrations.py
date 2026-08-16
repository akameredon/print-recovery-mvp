from __future__ import annotations

import sqlite3
from collections.abc import Callable

Migration = tuple[int, str, Callable[[sqlite3.Connection], None]]


def migration_1_initial_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            printer_model TEXT,
            rip_name TEXT,
            media_width_mm REAL,
            media_length_mm REAL,
            origin_x_mm REAL DEFAULT 0,
            origin_y_mm REAL DEFAULT 0,
            scale REAL DEFAULT 1,
            resolution TEXT,
            passes INTEGER,
            profile TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            y_mm REAL NOT NULL,
            band_mm REAL DEFAULT 1,
            state TEXT NOT NULL,
            evidence TEXT NOT NULL,
            confidence TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            source TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            selected_y_mm REAL,
            overlap_mm REAL,
            mode TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            confidence TEXT NOT NULL,
            operator_action TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        """)


def migration_2_add_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at);
        CREATE INDEX IF NOT EXISTS idx_checkpoints_job_y ON checkpoints(job_id, y_mm);
        CREATE INDEX IF NOT EXISTS idx_events_job_id ON events(job_id, id);
        CREATE INDEX IF NOT EXISTS idx_decisions_job_id ON decisions(job_id, id);
        """)


def migration_4_add_checkpoint_band_pass(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE checkpoints ADD COLUMN logical_band INTEGER")
    conn.execute("ALTER TABLE checkpoints ADD COLUMN pass_number INTEGER")


def migration_5_add_job_overlap(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE jobs ADD COLUMN overlap_mm REAL NOT NULL DEFAULT 5.0")


def migration_3_add_status_history(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS job_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            reason TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        CREATE INDEX IF NOT EXISTS idx_status_history_job_id ON job_status_history(job_id, id);
        """)


MIGRATIONS: list[Migration] = [
    (1, "initial_schema", migration_1_initial_schema),
    (2, "add_operational_indexes", migration_2_add_indexes),
    (3, "add_job_status_history", migration_3_add_status_history),
    (4, "add_checkpoint_band_pass", migration_4_add_checkpoint_band_pass),
    (5, "add_job_overlap", migration_5_add_job_overlap),
]


def run_migrations(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    applied_now: list[tuple[int, str]] = []
    for version, name, migration in MIGRATIONS:
        if version in applied:
            continue
        migration(conn)
        conn.execute("INSERT INTO schema_migrations(version,name) VALUES(?,?)", (version, name))
        applied_now.append((version, name))
    conn.commit()
    return applied_now


def applied_versions(conn: sqlite3.Connection) -> list[int]:
    return [
        row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")
    ]
