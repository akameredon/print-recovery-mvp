from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from PIL import Image, ImageDraw
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from adapters import SimulatedAdapter
from checkpoint_confidence import calculate_checkpoint_confidence
from config import load_config, resolve_path
from coordinate_conversion import media_mm_to_pixel
from evidence_bundle import build_evidence_bundle, render_handoff_markdown
from interruption_classification import classify_interruption
from job_manifest import build_job_manifest
from lifecycle_observer import observe_lifecycle
from logging_utils import configure_logging, set_correlation_id
from migrations import MIGRATIONS, applied_versions, run_migrations
from orientation_validation import validate_orientation_origin
from output_naming import continuation_output_name
from readiness_summary import summarize_readiness
from recovery_report import render_recovery_report
from recovery_safety import assess_recovery_safety
from registration_strip import generate_registration_strip
from signal_matrix import assess_signal_matrix

ROOT = Path(__file__).resolve().parent
CONFIG = load_config(ROOT)
APP_VERSION = "0.1.0"
DATA_DIR = resolve_path(ROOT, CONFIG["data_dir"])
OUTPUT_DIR = resolve_path(ROOT, CONFIG["output_dir"])
DB_PATH = DATA_DIR / "print_recovery.sqlite3"
LOG_PATH = DATA_DIR / "print_recovery.log"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = configure_logging(str(LOG_PATH), CONFIG["log_level"])
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = CONFIG["max_upload_mb"] * 1024 * 1024
app.secret_key = os.environ.get("PRINT_RECOVERY_SESSION_SECRET", "day61-local-session-key")
SESSION_TTL_SECONDS = int(os.environ.get("PRINT_RECOVERY_SESSION_TTL_SECONDS", "3600"))


@app.before_request
def begin_request():
    g.request_started = time.perf_counter()
    g.correlation_id = set_correlation_id(request.headers.get("X-Correlation-ID"))


@app.after_request
def finish_request(response):
    duration_ms = round(
        (time.perf_counter() - g.get("request_started", time.perf_counter())) * 1000, 2
    )
    logger.info(
        "request_completed",
        extra={
            "route": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    response.headers["X-Correlation-ID"] = g.get("correlation_id", "-")
    return response


def wants_json_error() -> bool:
    return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"


def error_response(message: str, status_code: int, error_code: str):
    payload = {
        "error": error_code,
        "message": message,
        "status": status_code,
        "correlation_id": g.get("correlation_id", "-"),
    }
    if wants_json_error():
        return jsonify(payload), status_code
    return render_template("error.html", **payload), status_code


@app.errorhandler(HTTPException)
def handle_http_error(error):
    logger.warning(
        "http_error",
        extra={"route": request.path, "status_code": error.code},
    )
    return error_response(
        error.description, error.code or 500, error.name.upper().replace(" ", "_")
    )


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("unhandled_exception", extra={"route": request.path, "status_code": 500})
    return error_response(
        "Internal server error. Use the correlation ID when requesting support.",
        500,
        "INTERNAL_ERROR",
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def init_db():
    conn = db()
    applied_now = run_migrations(conn)
    if applied_now:
        logger.info("database_migrations_applied", extra={"event_type": str(applied_now)})
    else:
        logger.debug("database_schema_current")
    conn.close()


def row_dict(row):
    return dict(row) if row else None


def record_event(conn, job_id, event_type, source, payload):
    serialized_payload = json.dumps(payload, sort_keys=True)
    previous = conn.execute(
        "SELECT event_type,source,payload FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1",
        (job_id,),
    ).fetchone()
    if previous and (previous["event_type"], previous["source"], previous["payload"]) == (
        event_type,
        source,
        serialized_payload,
    ):
        logger.info(
            "duplicate_domain_event_suppressed",
            extra={"job_id": job_id, "event_type": event_type},
        )
        return False
    conn.execute(
        "INSERT INTO events(job_id,event_type,source,payload,created_at) VALUES(?,?,?,?,?)",
        (job_id, event_type, source, serialized_payload, now()),
    )
    logger.info(
        "domain_event_recorded",
        extra={"job_id": job_id, "event_type": event_type},
    )
    return True


def record_status_transition(conn, job_id, to_status, reason, source, force=False):
    current = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not current:
        return False
    from_status = current["status"]
    if from_status == to_status and not force:
        return False
    conn.execute(
        "INSERT INTO job_status_history(job_id,from_status,to_status,reason,source,created_at) VALUES(?,?,?,?,?,?)",
        (job_id, from_status, to_status, reason, source, now()),
    )
    conn.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?", (to_status, now(), job_id))
    logger.info("job_status_transition", extra={"job_id": job_id, "event_type": to_status})
    return True


def latest_checkpoint(conn, job_id):
    return conn.execute(
        "SELECT * FROM checkpoints WHERE job_id=? ORDER BY y_mm DESC, id DESC LIMIT 1", (job_id,)
    ).fetchone()


def clock_consistency_check(conn, threshold_seconds=5.0, application_timestamp=None):
    application_time = datetime.fromisoformat(
        (application_timestamp or now()).replace("Z", "+00:00")
    )
    database_value = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')").fetchone()[0]
    database_time = datetime.fromisoformat(database_value)
    drift_seconds = round(abs((application_time - database_time).total_seconds()), 3)
    status = "ok" if drift_seconds <= threshold_seconds else "warning"
    return {
        "status": status,
        "clock_source": "application_utc_and_sqlite_utc",
        "application_timestamp": application_time.isoformat(),
        "database_timestamp": database_time.isoformat(),
        "drift_seconds": drift_seconds,
        "warning_threshold_seconds": threshold_seconds,
        "message": (
            "Clock sources are consistent"
            if status == "ok"
            else "Clock-source drift may affect event ordering"
        ),
    }


def diagnostics_snapshot():
    checks = {}
    try:
        conn = db()
        conn.execute("SELECT 1").fetchone()
        versions = applied_versions(conn)
        clock_check = clock_consistency_check(conn)
        conn.close()
        expected_versions = [version for version, _, _ in MIGRATIONS]
        checks["database"] = {
            "status": "ok",
            "schema_versions": versions,
            "expected_versions": expected_versions,
        }
        if versions != expected_versions:
            checks["database"] = {
                "status": "degraded",
                "schema_versions": versions,
                "expected_versions": expected_versions,
            }
        checks["clock"] = clock_check
    except Exception as error:
        logger.exception("diagnostics_database_failed")
        checks["database"] = {"status": "error", "error": str(error)}

    checks["paths"] = {
        "status": (
            "ok"
            if DATA_DIR.exists()
            and OUTPUT_DIR.exists()
            and os.access(DATA_DIR, os.W_OK)
            and os.access(OUTPUT_DIR, os.W_OK)
            else "degraded"
        ),
        "data_dir": str(DATA_DIR),
        "output_dir": str(OUTPUT_DIR),
        "log_path": str(LOG_PATH),
    }
    overall = "ok" if all(check["status"] == "ok" for check in checks.values()) else "degraded"
    return {
        "service": "print-recovery-mvp",
        "version": APP_VERSION,
        "status": overall,
        "timestamp": now(),
        "checks": checks,
        "configuration": {
            "host": CONFIG["host"],
            "port": CONFIG["port"],
            "log_level": CONFIG["log_level"],
            "max_upload_mb": CONFIG["max_upload_mb"],
        },
    }


@app.get("/healthz")
def healthz():
    snapshot = diagnostics_snapshot()
    status_code = 200 if snapshot["status"] == "ok" else 503
    return jsonify(snapshot), status_code


@app.get("/api/diagnostics")
def diagnostics():
    snapshot = diagnostics_snapshot()
    snapshot["request_correlation_id"] = g.get("correlation_id", "-")
    return jsonify(snapshot)


INTERRUPTION_REASONS = {
    "POWER_LOSS",
    "PROTECTION_TRIP",
    "COMMUNICATION_LOSS",
    "PRINTER_ERROR",
    "MATERIAL_ISSUE",
    "OPERATOR_ABORT",
    "UNKNOWN",
}


USER_ROLES = {"operator", "technician", "owner"}


def session_is_expired(issued_at: str | None, now_epoch: float | None = None) -> bool:
    if not issued_at:
        return True
    try:
        issued_epoch = float(issued_at)
    except (TypeError, ValueError):
        return True
    return (
        now_epoch if now_epoch is not None else time.time()
    ) - issued_epoch >= SESSION_TTL_SECONDS


def current_user(conn):
    user_id = session.get("user_id")
    if not user_id or session_is_expired(session.get("issued_at")):
        session.clear()
        return None
    if not user_id:
        return None
    row = conn.execute(
        "SELECT id,username,display_name,role,active,created_at FROM users WHERE id=?",
        (user_id,),
    ).fetchone()
    if not row or not row["active"]:
        session.pop("user_id", None)
        return None
    return row_dict(row)


def require_roles(conn, allowed_roles):
    user = current_user(conn)
    if not user:
        return None, error_response("Authentication is required", 401, "AUTHENTICATION_REQUIRED")
    if user["role"] not in allowed_roles:
        return None, error_response(
            "This action requires technician or owner permissions",
            403,
            "ROLE_FORBIDDEN",
        )
    return user, None


@app.get("/api/users")
def users_list():
    conn = db()
    users = [
        row_dict(row)
        for row in conn.execute(
            "SELECT id,username,display_name,role,active,created_at FROM users ORDER BY username"
        ).fetchall()
    ]
    active_user = current_user(conn)
    conn.close()
    return jsonify(users=users, current_user=active_user, roles=sorted(USER_ROLES))


@app.post("/api/users")
def create_user():
    payload = request.get_json(silent=True) or request.form
    username = str(payload.get("username", "")).strip().lower()
    display_name = str(payload.get("display_name", "")).strip()
    role = str(payload.get("role", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not username or not display_name or role not in USER_ROLES or not password:
        return error_response(
            "username, display_name, role and password are required",
            400,
            "INVALID_USER",
        )
    if len(username) > 80 or len(display_name) > 120:
        return error_response("username or display_name is too long", 400, "INVALID_USER")
    if len(password) < 8:
        return error_response("password must be at least 8 characters", 400, "WEAK_PASSWORD")
    user_id = uuid.uuid4().hex[:12]
    conn = db()
    try:
        conn.execute(
            "INSERT INTO users(id,username,display_name,role,active,created_at,password_hash) VALUES(?,?,?,?,?,?,?)",
            (user_id, username, display_name, role, 1, now(), generate_password_hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return error_response("username already exists", 409, "USER_EXISTS")
    user = row_dict(
        conn.execute(
            "SELECT id,username,display_name,role,active,created_at FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
    )
    conn.close()
    return jsonify(user=user), 201


@app.get("/api/session")
def get_session_user():
    conn = db()
    user = current_user(conn)
    conn.close()
    return jsonify(authenticated=bool(user), user=user)


@app.post("/api/session")
def select_session_user():
    payload = request.get_json(silent=True) or request.form
    username = str(payload.get("username", "")).strip().lower()
    password = str(payload.get("password", ""))
    conn = db()
    row = conn.execute(
        "SELECT id,username,display_name,role,active,created_at,password_hash FROM users WHERE username=? AND active=1",
        (username,),
    ).fetchone()
    if (
        not row
        or not row["password_hash"]
        or not check_password_hash(row["password_hash"], password)
    ):
        conn.close()
        return error_response("invalid username or password", 401, "INVALID_CREDENTIALS")
    login_time = now()
    conn.execute("UPDATE users SET last_login_at=? WHERE id=?", (login_time, row["id"]))
    conn.commit()
    user = {
        key: row[key] for key in ("id", "username", "display_name", "role", "active", "created_at")
    }
    conn.close()
    session.clear()
    session["user_id"] = user["id"]
    session["issued_at"] = str(time.time())
    session["last_login_at"] = login_time
    return jsonify(authenticated=True, user=user, expires_in_seconds=SESSION_TTL_SECONDS)


@app.post("/api/login")
def login():
    return select_session_user()


@app.delete("/api/session")
def clear_session_user():
    session.clear()
    return jsonify(authenticated=False, user=None)


PROFILE_REQUIRED_FIELDS = (
    "name",
    "manufacturer",
    "printer_model",
    "rip_name",
    "rip_version",
    "connection_mode",
    "job_input_path",
    "job_output_or_hotfolder",
)


def profile_payload(payload):
    values = {field: str(payload.get(field, "")).strip() for field in PROFILE_REQUIRED_FIELDS}
    missing = [field for field, value in values.items() if not value]
    if missing:
        return None, error_response(
            "Missing required profile fields: " + ", ".join(missing),
            400,
            "INVALID_PRINTER_PROFILE",
        )
    recovery_mode = str(payload.get("recovery_mode", "assisted_only")).strip().lower()
    if recovery_mode != "assisted_only":
        return None, error_response(
            "Only assisted_only recovery mode is supported by this MVP",
            400,
            "UNSAFE_RECOVERY_MODE",
        )
    raw_signals = payload.get("observable_signals", [])
    if isinstance(raw_signals, str):
        try:
            raw_signals = json.loads(raw_signals)
        except json.JSONDecodeError:
            raw_signals = [item.strip() for item in raw_signals.split(",") if item.strip()]
    if not isinstance(raw_signals, list) or not all(isinstance(item, str) for item in raw_signals):
        return None, error_response(
            "observable_signals must be a list of strings", 400, "INVALID_PRINTER_PROFILE"
        )
    values.update(
        recovery_mode=recovery_mode,
        observable_signals=raw_signals,
        physical_validation_required=bool(payload.get("physical_validation_required", True)),
        status=str(payload.get("status", "draft")).strip().lower() or "draft",
    )
    if values["status"] not in {"draft", "ready", "retired"}:
        return None, error_response(
            "status must be draft, ready or retired", 400, "INVALID_PRINTER_PROFILE"
        )
    return values, None


def public_profile(row):
    profile = row_dict(row)
    if profile:
        profile["observable_signals"] = json.loads(profile["observable_signals"] or "[]")
        profile["physical_validation_required"] = bool(profile["physical_validation_required"])
        profile.pop("active", None)
    return profile


@app.get("/api/printer-profiles")
def printer_profiles_list():
    conn = db()
    profiles = [
        public_profile(row)
        for row in conn.execute(
            "SELECT * FROM printer_profiles WHERE active=1 ORDER BY name"
        ).fetchall()
    ]
    conn.close()
    return jsonify(profiles=profiles, count=len(profiles))


@app.post("/api/printer-profiles")
def create_printer_profile():
    conn = db()
    _, auth_error = require_roles(conn, {"technician", "owner"})
    if auth_error:
        conn.close()
        return auth_error
    payload = request.get_json(silent=True) or request.form
    values, error = profile_payload(payload)
    if error:
        conn.close()
        return error
    profile_id = uuid.uuid4().hex[:12]
    timestamp = now()
    try:
        conn.execute(
            """INSERT INTO printer_profiles(
                id,name,manufacturer,printer_model,rip_name,rip_version,connection_mode,
                job_input_path,job_output_or_hotfolder,recovery_mode,observable_signals,
                physical_validation_required,status,active,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                profile_id,
                values["name"],
                values["manufacturer"],
                values["printer_model"],
                values["rip_name"],
                values["rip_version"],
                values["connection_mode"],
                values["job_input_path"],
                values["job_output_or_hotfolder"],
                values["recovery_mode"],
                json.dumps(values["observable_signals"], sort_keys=True),
                int(values["physical_validation_required"]),
                values["status"],
                1,
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return error_response("profile name already exists", 409, "PROFILE_EXISTS")
    profile = public_profile(
        conn.execute("SELECT * FROM printer_profiles WHERE id=?", (profile_id,)).fetchone()
    )
    conn.close()
    return jsonify(profile=profile), 201


@app.get("/api/printer-profiles/<profile_id>")
def printer_profile_detail(profile_id):
    conn = db()
    profile = public_profile(
        conn.execute(
            "SELECT * FROM printer_profiles WHERE id=? AND active=1", (profile_id,)
        ).fetchone()
    )
    conn.close()
    if not profile:
        return error_response("Printer profile not found", 404, "PROFILE_NOT_FOUND")
    return jsonify(profile=profile)


@app.patch("/api/printer-profiles/<profile_id>")
def update_printer_profile(profile_id):
    conn = db()
    _, auth_error = require_roles(conn, {"technician", "owner"})
    if auth_error:
        conn.close()
        return auth_error
    payload = request.get_json(silent=True) or request.form
    values, error = profile_payload(payload)
    if error:
        conn.close()
        return error
    if not conn.execute(
        "SELECT 1 FROM printer_profiles WHERE id=? AND active=1", (profile_id,)
    ).fetchone():
        conn.close()
        return error_response("Printer profile not found", 404, "PROFILE_NOT_FOUND")
    try:
        conn.execute(
            """UPDATE printer_profiles SET name=?,manufacturer=?,printer_model=?,rip_name=?,rip_version=?,
            connection_mode=?,job_input_path=?,job_output_or_hotfolder=?,recovery_mode=?,observable_signals=?,
            physical_validation_required=?,status=?,updated_at=? WHERE id=?""",
            (
                values["name"],
                values["manufacturer"],
                values["printer_model"],
                values["rip_name"],
                values["rip_version"],
                values["connection_mode"],
                values["job_input_path"],
                values["job_output_or_hotfolder"],
                values["recovery_mode"],
                json.dumps(values["observable_signals"], sort_keys=True),
                int(values["physical_validation_required"]),
                values["status"],
                now(),
                profile_id,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return error_response("profile name already exists", 409, "PROFILE_EXISTS")
    profile = public_profile(
        conn.execute("SELECT * FROM printer_profiles WHERE id=?", (profile_id,)).fetchone()
    )
    conn.close()
    return jsonify(profile=profile)


@app.delete("/api/printer-profiles/<profile_id>")
def retire_printer_profile(profile_id):
    conn = db()
    _, auth_error = require_roles(conn, {"technician", "owner"})
    if auth_error:
        conn.close()
        return auth_error
    updated = conn.execute(
        "UPDATE printer_profiles SET active=0,status='retired',updated_at=? WHERE id=? AND active=1",
        (now(), profile_id),
    ).rowcount
    conn.commit()
    conn.close()
    if not updated:
        return error_response("Printer profile not found", 404, "PROFILE_NOT_FOUND")
    return jsonify(profile_id=profile_id, status="retired")


JOB_FILTERS = {
    "all": None,
    "active": ("READY", "PRINTING", "RECOVERY_READY", "RECOVERING"),
    "interrupted": ("INTERRUPTED",),
    "completed": ("COMPLETED",),
}


def filtered_jobs(conn, filter_name, search="", date_from="", date_to=""):
    if filter_name not in JOB_FILTERS:
        raise ValueError("filter must be one of: all, active, interrupted, completed")
    where = []
    params = []
    statuses = JOB_FILTERS[filter_name]
    if statuses is not None:
        placeholders = ",".join("?" for _ in statuses)
        where.append(f"status IN ({placeholders})")
        params.extend(statuses)
    if search:
        where.append("(id LIKE ? OR file_name LIKE ? OR printer_model LIKE ? OR rip_name LIKE ?)")
        search_value = f"%{search}%"
        params.extend([search_value] * 4)
    for value, operator, error_message in (
        (date_from, ">=", "date_from must use YYYY-MM-DD"),
        (date_to, "<=", "date_to must use YYYY-MM-DD"),
    ):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError(error_message) from error
            where.append(f"date(created_at) {operator} date(?)")
            params.append(value)
    query = "SELECT * FROM jobs"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY updated_at DESC"
    return conn.execute(query, params).fetchall()


def job_query_values():
    return {
        "filter": request.args.get("filter", "all").strip().lower(),
        "search": request.args.get("q", "").strip(),
        "date_from": request.args.get("date_from", "").strip(),
        "date_to": request.args.get("date_to", "").strip(),
    }


@app.get("/api/jobs")
def jobs_list():
    values = job_query_values()
    try:
        conn = db()
        jobs = [
            row_dict(row)
            for row in filtered_jobs(
                conn,
                values["filter"],
                values["search"],
                values["date_from"],
                values["date_to"],
            )
        ]
        conn.close()
    except ValueError as error:
        return error_response(str(error), 400, "INVALID_JOB_QUERY")
    return jsonify(**values, count=len(jobs), jobs=jobs)


@app.route("/")
def index():
    values = job_query_values()
    try:
        conn = db()
        jobs = [
            row_dict(row)
            for row in filtered_jobs(
                conn,
                values["filter"],
                values["search"],
                values["date_from"],
                values["date_to"],
            )
        ]
        users = [
            row_dict(row)
            for row in conn.execute(
                "SELECT id,username,display_name,role,active,created_at FROM users ORDER BY username"
            ).fetchall()
        ]
        active_user = current_user(conn)
        profiles = [
            public_profile(row)
            for row in conn.execute(
                "SELECT * FROM printer_profiles WHERE active=1 ORDER BY name"
            ).fetchall()
        ]
        conn.close()
    except ValueError as error:
        return error_response(str(error), 400, "INVALID_JOB_QUERY")
    return render_template(
        "index.html",
        jobs=jobs,
        users=users,
        active_user=active_user,
        profiles=profiles,
        checkpoint_interval_mm=CONFIG["checkpoint_interval_mm"],
        **values,
    )


@app.post("/api/jobs")
def create_job():
    logger.info("job_creation_started", extra={"route": request.path})
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify(error="An image or source file is required for this prototype."), 400
    job_id = uuid.uuid4().hex[:12]
    safe_name = Path(file.filename).name
    source_path = DATA_DIR / f"{job_id}_{safe_name}"
    file.save(source_path)
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    form = request.form
    conn = db()
    conn.execute(
        """INSERT INTO jobs(id,file_name,source_path,source_hash,printer_model,rip_name,media_width_mm,media_length_mm,origin_x_mm,origin_y_mm,scale,resolution,passes,profile,overlap_mm,orientation,status,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            job_id,
            safe_name,
            str(source_path),
            digest,
            form.get("printer_model", "Unknown / not configured"),
            form.get("rip_name", "Unknown / not configured"),
            float(form.get("media_width_mm") or 0),
            float(form.get("media_length_mm") or 0),
            float(form.get("origin_x_mm") or 0),
            float(form.get("origin_y_mm") or 0),
            float(form.get("scale") or 1),
            form.get("resolution", "Not recorded"),
            int(form.get("passes") or 0),
            form.get("profile", "Not recorded"),
            float(form.get("overlap_mm") or 5.0),
            form.get("orientation", "top-left").strip().lower(),
            "READY",
            now(),
            now(),
        ),
    )
    conn.execute(
        "INSERT INTO job_status_history(job_id,from_status,to_status,reason,source,created_at) VALUES(?,?,?,?,?,?)",
        (job_id, None, "READY", "job_created", "operator", now()),
    )
    record_event(
        conn, job_id, "JOB_CREATED", "operator", {"file_name": safe_name, "source_hash": digest}
    )
    conn.commit()
    conn.close()
    logger.info("job_created", extra={"job_id": job_id})
    return redirect(url_for("index"))


@app.post("/api/jobs/<job_id>/checkpoint")
def checkpoint(job_id):
    logger.debug("checkpoint_received", extra={"job_id": job_id})
    payload = request.get_json(silent=True) or request.form
    y_mm = float(payload.get("y_mm", 0))
    band_mm = float(payload.get("band_mm", 1))
    logical_band = payload.get("logical_band")
    pass_number = payload.get("pass_number")
    try:
        logical_band = int(logical_band) if logical_band not in (None, "") else None
        pass_number = int(pass_number) if pass_number not in (None, "") else None
    except (TypeError, ValueError) as error:
        raise ValueError("logical_band and pass_number must be integers") from error
    if logical_band is not None and logical_band < 0:
        raise ValueError("logical_band must be non-negative")
    if pass_number is not None and pass_number < 0:
        raise ValueError("pass_number must be non-negative")
    state = payload.get("state", "PRINTING")
    evidence = payload.get("evidence", "transmitted")
    interval_mm = CONFIG["checkpoint_interval_mm"]
    confidence = {
        "prepared": "prepared",
        "transmitted": "transmitted",
        "acknowledged": "acknowledged",
        "physical": "physically_confirmed",
    }.get(evidence, "transmitted")
    conn = db()
    conn.execute(
        "INSERT INTO checkpoints(job_id,y_mm,band_mm,logical_band,pass_number,state,evidence,confidence,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (job_id, y_mm, band_mm, logical_band, pass_number, state, evidence, confidence, now()),
    )
    record_status_transition(conn, job_id, "PRINTING", "checkpoint_recorded", "operator_or_adapter")
    record_event(
        conn,
        job_id,
        "CHECKPOINT",
        "operator_or_adapter",
        {
            "y_mm": y_mm,
            "evidence": evidence,
            "interval_mm": interval_mm,
            "logical_band": logical_band,
            "pass_number": pass_number,
        },
    )
    conn.commit()
    conn.close()
    confidence_rules = calculate_checkpoint_confidence(
        {
            "evidence": evidence,
            "y_mm": y_mm,
            "logical_band": logical_band,
            "pass_number": pass_number,
        }
    )
    return jsonify(
        ok=True,
        job_id=job_id,
        y_mm=y_mm,
        confidence=confidence,
        confidence_rules=confidence_rules,
        checkpoint_interval_mm=interval_mm,
        logical_band=logical_band,
        pass_number=pass_number,
    )


@app.post("/api/jobs/<job_id>/interrupt")
def interrupt(job_id):
    logger.warning("interruption_received", extra={"job_id": job_id})
    payload = request.get_json(silent=True) or request.form
    reason = str(payload.get("reason", "UNKNOWN")).strip().upper()
    if reason not in INTERRUPTION_REASONS:
        return error_response(
            "reason must be one of: " + ", ".join(sorted(INTERRUPTION_REASONS)),
            400,
            "INVALID_INTERRUPTION_REASON",
        )
    source = str(payload.get("source", "operator")).strip() or "operator"
    note = str(payload.get("note", "")).strip()
    if len(note) > 1000:
        return error_response(
            "note must be 1000 characters or fewer", 400, "INVALID_INTERRUPTION_NOTE"
        )
    event_type = str(payload.get("event_type", reason)).strip() or reason
    classification = classify_interruption(reason, note, source)
    conn = db()
    job = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    record_status_transition(conn, job_id, "INTERRUPTED", event_type, source)
    record_event(
        conn,
        job_id,
        event_type,
        source,
        {"reason": reason, "note": note, "classification": classification},
    )
    conn.commit()
    conn.close()
    return jsonify(
        ok=True,
        status="INTERRUPTED",
        reason=reason,
        note=note,
        classification=classification,
    )


@app.get("/api/jobs/<job_id>")
def job_detail(job_id):
    conn = db()
    job = row_dict(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
    if not job:
        conn.close()
        return jsonify(error="Job not found"), 404
    checkpoints = [
        row_dict(r)
        for r in conn.execute(
            "SELECT * FROM checkpoints WHERE job_id=? ORDER BY y_mm", (job_id,)
        ).fetchall()
    ]
    events = [
        row_dict(r)
        for r in conn.execute(
            "SELECT * FROM events WHERE job_id=? ORDER BY id", (job_id,)
        ).fetchall()
    ]
    status_history = [
        row_dict(r)
        for r in conn.execute(
            "SELECT * FROM job_status_history WHERE job_id=? ORDER BY id", (job_id,)
        ).fetchall()
    ]
    conn.close()
    return jsonify(job=job, checkpoints=checkpoints, events=events, status_history=status_history)


@app.get("/api/jobs/<job_id>/manifest")
def job_manifest(job_id):
    output_format = request.args.get("format", "json").lower()
    if output_format not in {"json", "md", "markdown"}:
        return error_response("format must be json or md", 400, "INVALID_MANIFEST_FORMAT")
    conn = db()
    job = row_dict(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
    conn.close()
    if not job:
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    source_path = Path(job["source_path"])
    source_exists = source_path.exists()
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_exists else None
    manifest = build_job_manifest(
        job,
        source_exists=source_exists,
        actual_hash=actual_hash,
        captured_at=now(),
    )
    if output_format in {"md", "markdown"}:
        lines = [
            f"# Job Manifest — {job_id}",
            "",
            f"- File: `{job['file_name']}`",
            f"- Captured at: `{manifest['captured_at']}`",
            f"- Capture mode: `{manifest['capture_mode']}`",
            f"- Source integrity: **{manifest['job']['source_integrity']}**",
            f"- Printer/RIP: `{job['printer_model']}` / `{job['rip_name']}`",
            f"- Media: `{job['media_width_mm']} × {job['media_length_mm']} mm`",
            "",
            "> This manifest records host-side job evidence. It does not claim printer control or physical completion.",
            "",
        ]
        return Response("\n".join(lines), mimetype="text/markdown")
    return jsonify(manifest)


@app.get("/api/jobs/<job_id>/evidence-bundle")
def evidence_handoff_bundle(job_id):
    output_format = request.args.get("format", "json").lower()
    if output_format not in {"json", "md", "markdown"}:
        return error_response("format must be json or md", 400, "INVALID_BUNDLE_FORMAT")
    conn = db()
    job_row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job_row:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    job = row_dict(job_row)
    checkpoints = [
        row_dict(row)
        for row in conn.execute(
            "SELECT * FROM checkpoints WHERE job_id=? ORDER BY id", (job_id,)
        ).fetchall()
    ]
    events = [
        row_dict(row)
        for row in conn.execute(
            "SELECT * FROM events WHERE job_id=? ORDER BY id", (job_id,)
        ).fetchall()
    ]
    conn.close()
    source_path = Path(job["source_path"])
    source_exists = source_path.exists()
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_exists else None
    manifest = build_job_manifest(
        job, source_exists=source_exists, actual_hash=actual_hash, captured_at=now()
    )
    latest_checkpoint = checkpoints[-1] if checkpoints else {}
    report = {
        "generated_at": now(),
        "source_integrity": {"status": manifest["job"]["source_integrity"]},
        "selected_coordinate": {"y_mm": latest_checkpoint.get("y_mm")} if latest_checkpoint else {},
        "checkpoint_count": len(checkpoints),
        "event_count": len(events),
        "readiness": "review_required",
    }
    bundle = build_evidence_bundle(
        job=job,
        manifest=manifest,
        recovery_report=report,
        checkpoints=checkpoints,
        events=events,
    )
    if output_format in {"md", "markdown"}:
        return Response(render_handoff_markdown(bundle), mimetype="text/markdown")
    return jsonify(bundle)


@app.get("/api/jobs/<job_id>/integrity")
def source_integrity(job_id):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    source_path = Path(job["source_path"])
    if not source_path.exists():
        status = "missing"
        actual_hash = None
        record_event(conn, job_id, "SOURCE_MISSING", "integrity_checker", {})
        logger.warning("source_integrity_missing", extra={"job_id": job_id})
        response_code = 404
    else:
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        status = "verified" if actual_hash == job["source_hash"] else "changed"
        event_type = "SOURCE_VERIFIED" if status == "verified" else "SOURCE_CHANGED"
        record_event(conn, job_id, event_type, "integrity_checker", {"status": status})
        if status == "changed":
            logger.warning("source_integrity_changed", extra={"job_id": job_id})
        response_code = 200 if status == "verified" else 409
    conn.commit()
    conn.close()
    body = {
        "job_id": job_id,
        "file_name": job["file_name"],
        "status": status,
        "expected_hash": job["source_hash"],
        "actual_hash": actual_hash,
    }
    if status != "verified":
        body["error"] = "SOURCE_MISSING" if status == "missing" else "SOURCE_CHANGED"
        body["message"] = (
            "The stored source file is missing."
            if status == "missing"
            else "The stored source file hash does not match the recorded job hash."
        )
        body["correlation_id"] = g.get("correlation_id", "-")
    return jsonify(body), response_code


@app.get("/api/jobs/<job_id>/readiness")
def recovery_readiness(job_id):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")

    source_path = Path(job["source_path"])
    source_exists = source_path.exists()
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_exists else None
    integrity = (
        "missing"
        if not source_exists
        else ("verified" if actual_hash == job["source_hash"] else "changed")
    )
    checkpoint = latest_checkpoint(conn, job_id)
    interruption = conn.execute(
        "SELECT * FROM job_status_history WHERE job_id=? AND to_status='INTERRUPTED' ORDER BY id DESC LIMIT 1",
        (job_id,),
    ).fetchone()
    checkpoint_dict = row_dict(checkpoint)
    interruption_dict = row_dict(interruption)
    checkpoint_confidence = (
        calculate_checkpoint_confidence(checkpoint_dict) if checkpoint_dict else None
    )
    safety = assess_recovery_safety(
        source_integrity=integrity,
        has_checkpoint=checkpoint is not None,
        has_interruption=interruption is not None,
    )

    if safety["blockers"]:
        readiness = "blocked"
        reason = safety["blockers"][0]["message"]
    elif safety["warnings"]:
        readiness = "review_required"
        reason = safety["warnings"][0]["message"]
    else:
        readiness = "ready_for_operator_review"
        reason = "Source integrity, checkpoint evidence and interruption history are present."

    response = {
        "job_id": job_id,
        "readiness": readiness,
        "reason": reason,
        "job_status": job["status"],
        "source_integrity": {
            "status": integrity,
            "expected_hash": job["source_hash"],
            "actual_hash": actual_hash,
        },
        "checkpoint": checkpoint_dict,
        "checkpoint_confidence": checkpoint_confidence,
        "interruption": interruption_dict,
        "recovery_safety": safety,
        "operator_confirmation_required": True,
        "request_correlation_id": g.get("correlation_id", "-"),
    }
    conn.close()
    return jsonify(response)


@app.get("/api/jobs/<job_id>/readiness-summary")
def readiness_summary(job_id):
    detailed_response = recovery_readiness(job_id)
    if isinstance(detailed_response, tuple):
        detailed_response = detailed_response[0]
    if detailed_response.status_code != 200:
        return detailed_response
    return jsonify(summarize_readiness(detailed_response.get_json()))


@app.get("/api/jobs/<job_id>/recovery-report")
def recovery_report(job_id):
    output_format = request.args.get("format", "json").lower()
    if output_format not in {"json", "md", "markdown"}:
        return error_response("format must be json or md", 400, "INVALID_REPORT_FORMAT")
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    source_path = Path(job["source_path"])
    source_exists = source_path.exists()
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_exists else None
    integrity = (
        "missing"
        if not source_exists
        else ("verified" if actual_hash == job["source_hash"] else "changed")
    )
    checkpoint = latest_checkpoint(conn, job_id)
    checkpoint_dict = row_dict(checkpoint)
    checkpoint_confidence = (
        calculate_checkpoint_confidence(checkpoint_dict) if checkpoint_dict else None
    )
    decision = conn.execute(
        "SELECT * FROM decisions WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
    ).fetchone()
    decision_dict = row_dict(decision)
    selected_coordinate = None
    if decision_dict:
        selected_coordinate = {
            "y_mm": decision_dict.get("selected_y_mm"),
            "overlap_mm": decision_dict.get("overlap_mm"),
            "source": "decision",
        }
    elif checkpoint_dict:
        selected_coordinate = {
            "y_mm": checkpoint_dict.get("y_mm"),
            "overlap_mm": None,
            "source": "checkpoint",
        }
    interruption = None
    operator_review = None
    for row in conn.execute(
        "SELECT * FROM events WHERE job_id=? ORDER BY id", (job_id,)
    ).fetchall():
        try:
            details = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            details = {}
        if details.get("classification"):
            interruption = {
                "event_type": row["event_type"],
                "timestamp": row["created_at"],
                "details": details,
            }
        if row["event_type"] == "RECOVERY_REVIEWED":
            operator_review = {"timestamp": row["created_at"], **details}
    safety = assess_recovery_safety(
        source_integrity=integrity,
        has_checkpoint=checkpoint is not None,
        has_interruption=interruption is not None,
    )
    if safety["blockers"]:
        readiness = "blocked"
    elif safety["warnings"]:
        readiness = "review_required"
    else:
        readiness = "ready_for_operator_review"
    report = {
        "job_id": job_id,
        "file_name": job["file_name"],
        "generated_at": now(),
        "readiness": readiness,
        "selected_coordinate": selected_coordinate,
        "confidence": checkpoint_confidence,
        "source_integrity": {
            "status": integrity,
            "expected_hash": job["source_hash"],
            "actual_hash": actual_hash,
        },
        "checkpoint": checkpoint_dict,
        "interruption": interruption,
        "operator_review": operator_review,
        "decision": decision_dict,
        "recovery_safety": safety,
    }
    conn.close()
    if output_format in {"md", "markdown"}:
        return Response(render_recovery_report(report), mimetype="text/markdown")
    return jsonify(report)


@app.get("/api/jobs/<job_id>/timeline")
def recovery_timeline(job_id):
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return error_response("limit must be an integer", 400, "INVALID_LIMIT")
    if limit < 1 or limit > 500:
        return error_response("limit must be between 1 and 500", 400, "INVALID_LIMIT")

    conn = db()
    if not conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone():
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")

    timeline = []
    for row in conn.execute(
        "SELECT * FROM job_status_history WHERE job_id=?", (job_id,)
    ).fetchall():
        timeline.append(
            {
                "id": row["id"],
                "kind": "status_transition",
                "timestamp": row["created_at"],
                "source": row["source"],
                "event": row["to_status"],
                "details": {
                    "from_status": row["from_status"],
                    "to_status": row["to_status"],
                    "reason": row["reason"],
                },
            }
        )
    for row in conn.execute("SELECT * FROM checkpoints WHERE job_id=?", (job_id,)).fetchall():
        timeline.append(
            {
                "id": row["id"],
                "kind": "checkpoint",
                "timestamp": row["created_at"],
                "source": "checkpoint_recorder",
                "event": "CHECKPOINT",
                "details": {
                    "y_mm": row["y_mm"],
                    "band_mm": row["band_mm"],
                    "state": row["state"],
                    "evidence": row["evidence"],
                    "confidence": row["confidence"],
                },
            }
        )
    for row in conn.execute("SELECT * FROM events WHERE job_id=?", (job_id,)).fetchall():
        try:
            payload = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            payload = {"raw": row["payload"]}
        timeline.append(
            {
                "id": row["id"],
                "kind": "event",
                "timestamp": row["created_at"],
                "source": row["source"],
                "event": row["event_type"],
                "details": payload,
            }
        )
    for row in conn.execute("SELECT * FROM decisions WHERE job_id=?", (job_id,)).fetchall():
        timeline.append(
            {
                "id": row["id"],
                "kind": "decision",
                "timestamp": row["created_at"],
                "source": "recovery_assistant",
                "event": row["recommendation"],
                "details": {
                    "selected_y_mm": row["selected_y_mm"],
                    "overlap_mm": row["overlap_mm"],
                    "mode": row["mode"],
                    "confidence": row["confidence"],
                    "operator_action": row["operator_action"],
                },
            }
        )
    conn.close()
    timeline.sort(key=lambda item: (item["timestamp"], item["kind"], item["id"]))
    total = len(timeline)
    return jsonify(
        job_id=job_id,
        total=total,
        limit=limit,
        truncated=total > limit,
        items=timeline[-limit:],
        request_correlation_id=g.get("correlation_id", "-"),
    )


@app.get("/api/jobs/<job_id>/events/raw")
def export_raw_events(job_id):
    export_format = request.args.get("format", "jsonl").lower()
    if export_format != "jsonl":
        return error_response("format must be jsonl", 400, "INVALID_RAW_EVENT_FORMAT")
    conn = db()
    job_exists = conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job_exists:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    rows = conn.execute(
        "SELECT id,job_id,event_type,source,payload,created_at FROM events WHERE job_id=? ORDER BY id",
        (job_id,),
    ).fetchall()
    conn.close()
    lines = []
    for row in rows:
        lines.append(
            json.dumps(
                {
                    "id": row["id"],
                    "job_id": row["job_id"],
                    "event_type": row["event_type"],
                    "source": row["source"],
                    "payload_raw": row["payload"],
                    "created_at": row["created_at"],
                },
                separators=(",", ":"),
            )
        )
    filename = f"{job_id}_raw_events.jsonl"
    return Response(
        "\n".join(lines) + ("\n" if lines else ""),
        mimetype="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/jobs/<job_id>/signals/assess")
def assess_job_signals(job_id):
    payload = request.get_json(silent=True) or {}
    signals = payload.get("signals")
    source = (
        str(payload.get("source", "operator_signal_assessment")).strip()
        or "operator_signal_assessment"
    )
    if not isinstance(signals, list):
        return error_response("signals must be a list", 400, "INVALID_SIGNAL_LIST")
    assessment = assess_signal_matrix(signals)
    conn = db()
    if not conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone():
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    record_event(
        conn,
        job_id,
        "SIGNAL_MATRIX_ASSESSED",
        source,
        {"source": source, "signals": signals, "assessment": assessment},
    )
    conn.commit()
    conn.close()
    return jsonify(ok=True, job_id=job_id, source=source, assessment=assessment)


@app.post("/api/jobs/<job_id>/lifecycle/observe")
def observe_job_lifecycle(job_id):
    payload = request.get_json(silent=True) or {}
    events = payload.get("events")
    source = (
        str(payload.get("source", "rip_lifecycle_observer")).strip() or "rip_lifecycle_observer"
    )
    if not isinstance(events, list) or not events:
        return error_response("events must be a non-empty list", 400, "INVALID_LIFECYCLE_EVENTS")
    observation = observe_lifecycle(events)
    conn = db()
    if not conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone():
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    if observation["status"] == "invalid":
        conn.close()
        return jsonify(ok=False, job_id=job_id, source=source, observation=observation), 400
    record_event(
        conn,
        job_id,
        "RIP_LIFECYCLE_OBSERVED",
        source,
        {"source": source, "events": events, "observation": observation},
    )
    conn.commit()
    conn.close()
    return jsonify(ok=True, job_id=job_id, source=source, observation=observation)


@app.post("/api/jobs/<job_id>/adapter/simulate")
def simulate_adapter_event(job_id):
    payload = request.get_json(silent=True) or {}
    adapter = SimulatedAdapter()
    try:
        event = adapter.emit(payload.get("event_type", ""), payload.get("payload", {}))
    except (TypeError, ValueError) as error:
        return error_response(str(error), 400, "INVALID_ADAPTER_EVENT")
    conn = db()
    job_exists = conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job_exists:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    record_event(
        conn,
        job_id,
        f"ADAPTER_{event.event_type}",
        event.source,
        {**event.payload, "emitted_at": event.emitted_at},
    )
    conn.commit()
    conn.close()
    return jsonify(
        ok=True,
        job_id=job_id,
        adapter=adapter.name,
        event_type=event.event_type,
        source=event.source,
        payload=event.payload,
        emitted_at=event.emitted_at,
    )


@app.get("/api/jobs/<job_id>/status-history")
def status_history(job_id):
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))
    except ValueError:
        return error_response("page and per_page must be integers", 400, "INVALID_PAGINATION")
    if page < 1 or per_page < 1 or per_page > 100:
        return error_response(
            "page must be at least 1 and per_page must be between 1 and 100",
            400,
            "INVALID_PAGINATION",
        )

    conn = db()
    job_exists = conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job_exists:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    total = conn.execute(
        "SELECT COUNT(*) FROM job_status_history WHERE job_id=?", (job_id,)
    ).fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT * FROM job_status_history WHERE job_id=? ORDER BY id LIMIT ? OFFSET ?",
        (job_id, per_page, offset),
    ).fetchall()
    conn.close()
    pages = (total + per_page - 1) // per_page if total else 0
    return jsonify(
        job_id=job_id,
        items=[row_dict(row) for row in rows],
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_previous=page > 1 and pages > 0,
    )


@app.get("/api/jobs/<job_id>/status-history/export")
def export_status_history(job_id):
    export_format = request.args.get("format", "json").lower()
    if export_format not in {"json", "csv"}:
        return error_response("format must be json or csv", 400, "INVALID_EXPORT_FORMAT")
    conn = db()
    job_exists = conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job_exists:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    rows = [
        row_dict(row)
        for row in conn.execute(
            "SELECT * FROM job_status_history WHERE job_id=? ORDER BY id", (job_id,)
        ).fetchall()
    ]
    conn.close()
    filename = f"{job_id}_status_history.{export_format}"
    if export_format == "json":
        response = jsonify(job_id=job_id, items=rows, total=len(rows), format="json")
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    buffer = io.StringIO()
    fieldnames = ["id", "job_id", "from_status", "to_status", "reason", "source", "created_at"]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows({key: row.get(key) for key in fieldnames} for row in rows)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/jobs/<job_id>/recommendation")
def recommendation(job_id):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    cp = latest_checkpoint(conn, job_id)
    if not job:
        conn.close()
        return jsonify(error="Job not found"), 404
    if not cp:
        rec, confidence, mode, reason = "RESTART", "none", "assisted", "No checkpoint exists."
        selected = None
    elif cp["confidence"] == "physically_confirmed":
        rec, confidence, mode, reason = (
            "CONTINUE",
            "high",
            "certified_candidate",
            "Physical position was confirmed; adapter validation is still required.",
        )
        selected = cp["y_mm"]
    elif cp["confidence"] == "acknowledged":
        rec, confidence, mode, reason = (
            "TEST_FIRST",
            "medium",
            "assisted",
            "Printer acknowledgement exists, but physical output may include buffering.",
        )
        selected = cp["y_mm"]
    else:
        rec, confidence, mode, reason = (
            "TEST_FIRST",
            "low",
            "assisted",
            "Only host-side progress is known; use a registration strip or restart.",
        )
        selected = cp["y_mm"]
    conn.close()
    return jsonify(
        job_id=job_id,
        recommendation=rec,
        confidence=confidence,
        mode=mode,
        reason=reason,
        selected_y_mm=selected,
        overlap_mm=5,
    )


@app.get("/api/jobs/<job_id>/orientation")
def validate_job_orientation(job_id):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    source_path = Path(job["source_path"])
    try:
        with Image.open(source_path) as source:
            result = validate_orientation_origin(
                image_width_px=source.width,
                image_height_px=source.height,
                media_width_mm=float(job["media_width_mm"] or 0),
                media_length_mm=float(job["media_length_mm"] or 0),
                origin_x_mm=float(job["origin_x_mm"] or 0),
                origin_y_mm=float(job["origin_y_mm"] or 0),
                orientation=job["orientation"],
            )
    except (OSError, TypeError, ValueError) as error:
        conn.close()
        return error_response(
            f"Orientation validation failed: {error}", 400, "ORIENTATION_VALIDATION_FAILED"
        )
    conn.close()
    return jsonify(ok=True, job_id=job_id, **result)


@app.post("/api/jobs/<job_id>/overlap")
def update_job_overlap(job_id):
    payload = request.get_json(silent=True) or request.form
    try:
        overlap_mm = float(payload.get("overlap_mm", 5))
        if overlap_mm < 0:
            raise ValueError("overlap_mm must be non-negative")
    except (TypeError, ValueError) as error:
        return error_response(str(error), 400, "INVALID_OVERLAP")
    conn = db()
    job = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    conn.execute(
        "UPDATE jobs SET overlap_mm=?,updated_at=? WHERE id=?", (overlap_mm, now(), job_id)
    )
    record_event(conn, job_id, "JOB_OVERLAP_UPDATED", "operator", {"overlap_mm": overlap_mm})
    conn.commit()
    conn.close()
    return jsonify(ok=True, job_id=job_id, overlap_mm=overlap_mm)


@app.get("/api/jobs/<job_id>/continuation-preview")
def continuation_preview(job_id):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    checkpoint = latest_checkpoint(conn, job_id)
    conn.close()
    try:
        selected_y_mm = float(request.args.get("y_mm", checkpoint["y_mm"] if checkpoint else 0))
        overlap_mm = float(request.args.get("overlap_mm", job["overlap_mm"] or 5))
        if selected_y_mm < 0 or overlap_mm < 0:
            raise ValueError("y_mm and overlap_mm must be non-negative")
        source_path = Path(job["source_path"])
        with Image.open(source_path) as source:
            if source.height <= 0 or source.width <= 0:
                raise ValueError("Image has no usable dimensions")
            media_length_mm = max(float(job["media_length_mm"] or source.height), 1.0)
            selected_y_mm = min(selected_y_mm, media_length_mm)
            uncertain_start_mm = max(0.0, selected_y_mm - overlap_mm)
            uncertain_end_mm = min(media_length_mm, selected_y_mm + overlap_mm)
            selected_px = media_mm_to_pixel(selected_y_mm, media_length_mm, source.height)
            overlap_px = media_mm_to_pixel(overlap_mm, media_length_mm, source.height, clamp=False)
            uncertain_start_px = max(0, selected_px - overlap_px)
            uncertain_end_px = min(source.height, selected_px + overlap_px)
            preview_width = min(720, source.width)
            preview_height = max(1, int(source.height * preview_width / source.width))
            preview = source.convert("RGBA").resize((preview_width, preview_height))
            overlay = Image.new("RGBA", preview.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            scale = preview_height / source.height
            regions = [
                ("printed", 0, uncertain_start_px, (31, 122, 77, 92)),
                ("uncertain", uncertain_start_px, uncertain_end_px, (214, 139, 0, 120)),
                ("remaining", uncertain_end_px, source.height, (20, 93, 160, 92)),
            ]
            region_output = []
            for label, start_px, end_px, color in regions:
                top = int(start_px * scale)
                bottom = max(top + (1 if end_px > start_px else 0), int(end_px * scale))
                if end_px > start_px:
                    draw.rectangle((0, top, preview_width, bottom), fill=color)
                region_output.append(
                    {
                        "label": label,
                        "start_y_mm": round(
                            (
                                0.0
                                if label == "printed"
                                else (
                                    uncertain_start_mm if label == "uncertain" else uncertain_end_mm
                                )
                            ),
                            2,
                        ),
                        "end_y_mm": round(
                            (
                                uncertain_start_mm
                                if label == "printed"
                                else (uncertain_end_mm if label == "uncertain" else media_length_mm)
                            ),
                            2,
                        ),
                        "present": end_px > start_px,
                    }
                )
            selected_line = int(selected_px * scale)
            draw.line(
                (0, selected_line, preview_width, selected_line), fill=(166, 35, 35, 255), width=2
            )
            preview = Image.alpha_composite(preview, overlay).convert("RGB")
            preview_name = f"{job_id}_continuation_preview_{selected_y_mm:.1f}mm.png"
            preview.save(OUTPUT_DIR / preview_name)
    except (OSError, TypeError, ValueError) as error:
        return error_response(f"Continuation preview failed: {error}", 400, "PREVIEW_FAILED")
    return jsonify(
        ok=True,
        job_id=job_id,
        selected_y_mm=selected_y_mm,
        overlap_mm=overlap_mm,
        regions=region_output,
        preview_file=preview_name,
        preview_url=f"/outputs/{preview_name}",
        operator_confirmation_required=True,
    )


@app.post("/api/jobs/<job_id>/registration-strip")
def registration_strip(job_id):
    payload = request.get_json(silent=True) or request.form
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    try:
        selected_y_mm = float(payload.get("y_mm", 0))
        strip_height_mm = float(
            payload.get("strip_height_mm", max(10.0, float(job["overlap_mm"] or 5) * 2))
        )
        if selected_y_mm < 0 or strip_height_mm <= 0:
            raise ValueError("y_mm must be non-negative and strip_height_mm must be positive")
        version = (
            conn.execute(
                "SELECT COUNT(*) FROM events WHERE job_id=? AND event_type='REGISTRATION_STRIP_GENERATED'",
                (job_id,),
            ).fetchone()[0]
            + 1
        )
        source_token = "".join(
            character for character in job["source_hash"] if character.isalnum()
        )[:12]
        output_name = f"registration_strip-v{version:03d}_{job_id}_{source_token}_at-{selected_y_mm:.1f}mm.png"
        output_path = OUTPUT_DIR / output_name
        while output_path.exists():
            version += 1
            output_name = f"registration_strip-v{version:03d}_{job_id}_{source_token}_at-{selected_y_mm:.1f}mm.png"
            output_path = OUTPUT_DIR / output_name
        details = generate_registration_strip(
            Path(job["source_path"]),
            output_path,
            selected_y_mm=selected_y_mm,
            media_length_mm=max(float(job["media_length_mm"] or 0), 1.0),
            strip_height_mm=strip_height_mm,
        )
    except (OSError, TypeError, ValueError) as error:
        conn.close()
        return error_response(
            f"Registration strip generation failed: {error}", 400, "REGISTRATION_STRIP_FAILED"
        )
    record_event(
        conn,
        job_id,
        "REGISTRATION_STRIP_GENERATED",
        "recovery_engine",
        {
            "file": output_name,
            "version": version,
            "source_hash": job["source_hash"],
            "selected_y_mm": selected_y_mm,
            "strip_height_mm": strip_height_mm,
        },
    )
    conn.commit()
    conn.close()
    return jsonify(
        ok=True,
        job_id=job_id,
        file=output_name,
        url=f"/outputs/{output_name}",
        version=version,
        source_hash=job["source_hash"],
        **details,
        operator_confirmation_required=True,
    )


@app.get("/api/jobs/<job_id>/registration-strip/review")
def registration_strip_review_summary(job_id):
    conn = db()
    job = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    reviews = []
    for row in conn.execute(
        "SELECT * FROM events WHERE job_id=? AND event_type='REGISTRATION_STRIP_REVIEWED' ORDER BY id",
        (job_id,),
    ).fetchall():
        try:
            details = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            details = {"raw": row["payload"]}
        reviews.append(
            {
                "id": row["id"],
                "timestamp": row["created_at"],
                "source": row["source"],
                "details": details,
            }
        )
    conn.close()
    latest = reviews[-1] if reviews else None
    return jsonify(
        ok=True,
        job_id=job_id,
        review_state=latest["details"]["result"] if latest else "pending",
        latest_review=latest,
        reviews=reviews,
        operator_confirmation_required=latest is None,
    )


@app.post("/api/jobs/<job_id>/registration-strip/review")
def review_registration_strip(job_id):
    payload = request.get_json(silent=True) or request.form
    result = str(payload.get("result", "")).strip().lower()
    note = str(payload.get("note", "")).strip()
    file_name = str(payload.get("file", "")).strip()
    if result not in {"aligned", "misaligned", "uncertain"}:
        return error_response(
            "result must be aligned, misaligned or uncertain",
            400,
            "INVALID_REGISTRATION_RESULT",
        )
    if len(note) > 1000:
        return error_response("note must be 1000 characters or fewer", 400, "INVALID_REVIEW_NOTE")
    conn = db()
    job = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    if not file_name:
        latest_strip = conn.execute(
            "SELECT payload FROM events WHERE job_id=? AND event_type='REGISTRATION_STRIP_GENERATED' ORDER BY id DESC LIMIT 1",
            (job_id,),
        ).fetchone()
        if latest_strip:
            try:
                file_name = json.loads(latest_strip["payload"])["file"]
            except (TypeError, KeyError, json.JSONDecodeError):
                file_name = ""
    if not file_name:
        conn.close()
        return error_response(
            "Generate a registration strip before reviewing it", 409, "NO_REGISTRATION_STRIP"
        )
    generated = conn.execute(
        "SELECT 1 FROM events WHERE job_id=? AND event_type='REGISTRATION_STRIP_GENERATED' AND payload LIKE ? LIMIT 1",
        (job_id, f'%"file": "{file_name}"%'),
    ).fetchone()
    if not generated:
        conn.close()
        return error_response(
            "Registration strip does not belong to this job", 400, "UNKNOWN_REGISTRATION_STRIP"
        )
    details = {"result": result, "note": note, "file": file_name}
    record_event(conn, job_id, "REGISTRATION_STRIP_REVIEWED", "operator", details)
    conn.commit()
    conn.close()
    return jsonify(ok=True, job_id=job_id, **details, operator_confirmation_required=False)


@app.post("/api/jobs/<job_id>/continuation")
def continuation(job_id):
    logger.info("continuation_generation_started", extra={"job_id": job_id})
    payload = request.get_json(silent=True) or request.form
    y_mm = float(payload.get("y_mm", 0))
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return jsonify(error="Job not found"), 404
    overlap_mm = float(payload.get("overlap_mm", job["overlap_mm"] or 5))
    if overlap_mm < 0:
        conn.close()
        return error_response("overlap_mm must be non-negative", 400, "INVALID_OVERLAP")
    source_path = Path(job["source_path"])
    source_exists = source_path.exists()
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_exists else None
    checkpoint = latest_checkpoint(conn, job_id)
    safety = assess_recovery_safety(
        source_integrity=(
            "missing"
            if not source_exists
            else ("verified" if actual_hash == job["source_hash"] else "changed")
        ),
        has_checkpoint=checkpoint is not None,
        has_interruption=True,
    )
    if not safety["safe_to_generate"]:
        conn.close()
        return (
            jsonify(
                error="RECOVERY_BLOCKED",
                message="Continuation generation is blocked until recovery evidence is restored or reviewed.",
                job_id=job_id,
                recovery_safety=safety,
            ),
            409,
        )
    generated_count = conn.execute(
        "SELECT COUNT(*) FROM decisions WHERE job_id=? AND operator_action='generated_continuation'",
        (job_id,),
    ).fetchone()[0]
    version = int(generated_count) + 1
    output_name = continuation_output_name(job_id, job["source_hash"], version, y_mm, overlap_mm)
    output_path = OUTPUT_DIR / output_name
    while output_path.exists():
        version += 1
        output_name = continuation_output_name(
            job_id, job["source_hash"], version, y_mm, overlap_mm
        )
        output_path = OUTPUT_DIR / output_name
    try:
        with Image.open(source_path) as im:
            if im.height <= 0:
                raise ValueError("Image has no height")
            media_length_mm = max(float(job["media_length_mm"] or im.height), 1.0)
            start_px = min(
                im.height - 1,
                media_mm_to_pixel(y_mm, media_length_mm, im.height),
            )
            overlap_px = media_mm_to_pixel(overlap_mm, media_length_mm, im.height, clamp=False)
            crop_start = max(0, start_px - overlap_px)
            im.crop((0, crop_start, im.width, im.height)).save(output_path)
    except Exception as exc:
        conn.close()
        return jsonify(error=f"Continuation generation failed: {exc}"), 400
    conn.execute(
        "INSERT INTO decisions(job_id,selected_y_mm,overlap_mm,mode,recommendation,confidence,operator_action,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (
            job_id,
            y_mm,
            overlap_mm,
            "assisted",
            "TEST_FIRST",
            "operator_selected",
            "generated_continuation",
            now(),
        ),
    )
    record_status_transition(
        conn, job_id, "RECOVERY_READY", "continuation_generated", "recovery_engine"
    )
    record_event(
        conn,
        job_id,
        "CONTINUATION_GENERATED",
        "recovery_engine",
        {
            "file": output_name,
            "version": version,
            "source_hash": job["source_hash"],
            "y_mm": y_mm,
            "overlap_mm": overlap_mm,
        },
    )
    conn.commit()
    conn.close()
    return jsonify(
        ok=True,
        file=output_name,
        url=f"/outputs/{output_name}",
        selected_y_mm=y_mm,
        overlap_mm=overlap_mm,
        version=version,
        source_hash=job["source_hash"],
    )


@app.get("/api/jobs/<job_id>/review")
def review_summary(job_id):
    conn = db()
    job = conn.execute("SELECT id,status FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    decision = conn.execute(
        "SELECT * FROM decisions WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
    ).fetchone()
    if not decision:
        conn.close()
        return error_response("No recovery decision exists to review", 409, "NO_DECISION")
    review_events = []
    for row in conn.execute(
        "SELECT * FROM events WHERE job_id=? AND event_type='RECOVERY_REVIEWED' ORDER BY id",
        (job_id,),
    ).fetchall():
        try:
            payload = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            payload = {"raw": row["payload"]}
        review_events.append(
            {
                "id": row["id"],
                "timestamp": row["created_at"],
                "source": row["source"],
                "details": payload,
            }
        )
    operator_action = decision["operator_action"] or ""
    review_state = (
        "approved"
        if operator_action.startswith("approved")
        else "rejected" if operator_action.startswith("rejected") else "pending"
    )
    response = {
        "job_id": job_id,
        "job_status": job["status"],
        "review_state": review_state,
        "decision": row_dict(decision),
        "review_events": review_events,
        "operator_confirmation_required": review_state == "pending",
        "request_correlation_id": g.get("correlation_id", "-"),
    }
    conn.close()
    return jsonify(response)


@app.post("/api/jobs/<job_id>/review")
def review_recovery(job_id):
    payload = request.get_json(silent=True) or request.form
    action = str(payload.get("action", "")).strip().lower()
    note = str(payload.get("note", "")).strip()
    if action not in {"approved", "rejected"}:
        return error_response(
            "action must be either approved or rejected", 400, "INVALID_REVIEW_ACTION"
        )
    if len(note) > 1000:
        return error_response("note must be 1000 characters or fewer", 400, "INVALID_REVIEW_NOTE")

    conn = db()
    job = conn.execute("SELECT id,status FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return error_response("Job not found", 404, "JOB_NOT_FOUND")
    decision = conn.execute(
        "SELECT * FROM decisions WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
    ).fetchone()
    if not decision:
        conn.close()
        return error_response("No recovery decision exists to review", 409, "NO_DECISION")

    operator_action = f"{action}: {note}" if note else action
    conn.execute(
        "UPDATE decisions SET operator_action=? WHERE id=?", (operator_action, decision["id"])
    )
    record_event(
        conn,
        job_id,
        "RECOVERY_REVIEWED",
        "operator",
        {"action": action, "note": note, "decision_id": decision["id"]},
    )
    conn.commit()
    conn.close()
    logger.info("recovery_review_recorded", extra={"job_id": job_id, "event_type": action})
    return jsonify(
        ok=True,
        job_id=job_id,
        decision_id=decision["id"],
        action=action,
        note=note,
        job_status=job["status"],
        operator_confirmation_required=True,
        request_correlation_id=g.get("correlation_id", "-"),
    )


@app.get("/outputs/<path:name>")
def outputs(name):
    return send_from_directory(OUTPUT_DIR, name, as_attachment=True)


init_db()

if __name__ == "__main__":
    app.run(host=CONFIG["host"], port=CONFIG["port"], debug=False)
