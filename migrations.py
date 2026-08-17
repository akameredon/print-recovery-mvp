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


def migration_6_add_orientation(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE jobs ADD COLUMN orientation TEXT NOT NULL DEFAULT 'top-left'")


def migration_7_add_local_users(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('operator', 'technician', 'owner')),
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        """)


def migration_8_add_password_auth(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    conn.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")


def migration_9_add_printer_profiles(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS printer_profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            manufacturer TEXT NOT NULL,
            printer_model TEXT NOT NULL,
            rip_name TEXT NOT NULL,
            rip_version TEXT NOT NULL,
            connection_mode TEXT NOT NULL,
            job_input_path TEXT NOT NULL,
            job_output_or_hotfolder TEXT NOT NULL,
            recovery_mode TEXT NOT NULL DEFAULT 'assisted_only',
            observable_signals TEXT NOT NULL DEFAULT '[]',
            physical_validation_required INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'draft',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_printer_profiles_active ON printer_profiles(active);
        """)


def migration_10_add_audit_log(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id TEXT,
            actor_username TEXT,
            actor_role TEXT,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(actor_user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at, id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
        CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
        """)


def migration_11_add_workspaces(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        INSERT OR IGNORE INTO workspaces(id,name,active,created_at)
        VALUES('ws-default','Default shop',1,CURRENT_TIMESTAMP);
        """)
    conn.execute("ALTER TABLE users ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'ws-default'")
    conn.execute("ALTER TABLE jobs ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'ws-default'")
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_users_workspace ON users(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_workspace ON jobs(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_workspaces_active ON workspaces(active);
        """)


def migration_12_add_adapter_configurations(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS adapter_configurations (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            adapter_type TEXT NOT NULL,
            printer_profile_id TEXT,
            connection_mode TEXT NOT NULL,
            trace_or_endpoint TEXT NOT NULL,
            settings TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'draft',
            enabled INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(workspace_id, name),
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
        );
        CREATE INDEX IF NOT EXISTS idx_adapter_config_workspace ON adapter_configurations(workspace_id, enabled);
        """)


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
    (6, "add_orientation", migration_6_add_orientation),
    (7, "add_local_users", migration_7_add_local_users),
    (8, "add_password_auth", migration_8_add_password_auth),
    (9, "add_printer_profiles", migration_9_add_printer_profiles),
    (10, "add_audit_log", migration_10_add_audit_log),
    (11, "add_workspaces", migration_11_add_workspaces),
    (12, "add_adapter_configurations", migration_12_add_adapter_configurations),
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
