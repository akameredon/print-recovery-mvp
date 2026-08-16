from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
DB_PATH = DATA_DIR / "print_recovery.sqlite3"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript(
        """
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
        """
    )
    conn.commit()
    conn.close()


def row_dict(row):
    return dict(row) if row else None


def record_event(conn, job_id, event_type, source, payload):
    conn.execute(
        "INSERT INTO events(job_id,event_type,source,payload,created_at) VALUES(?,?,?,?,?)",
        (job_id, event_type, source, json.dumps(payload), now()),
    )


def latest_checkpoint(conn, job_id):
    return conn.execute(
        "SELECT * FROM checkpoints WHERE job_id=? ORDER BY y_mm DESC, id DESC LIMIT 1", (job_id,)
    ).fetchone()


@app.route("/")
def index():
    conn = db()
    jobs = [row_dict(r) for r in conn.execute("SELECT * FROM jobs ORDER BY updated_at DESC").fetchall()]
    conn.close()
    return render_template("index.html", jobs=jobs)


@app.post("/api/jobs")
def create_job():
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
        """INSERT INTO jobs(id,file_name,source_path,source_hash,printer_model,rip_name,media_width_mm,media_length_mm,origin_x_mm,origin_y_mm,scale,resolution,passes,profile,status,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
            "READY",
            now(),
            now(),
        ),
    )
    record_event(conn, job_id, "JOB_CREATED", "operator", {"file_name": safe_name, "source_hash": digest})
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.post("/api/jobs/<job_id>/checkpoint")
def checkpoint(job_id):
    payload = request.get_json(silent=True) or request.form
    y_mm = float(payload.get("y_mm", 0))
    band_mm = float(payload.get("band_mm", 1))
    state = payload.get("state", "PRINTING")
    evidence = payload.get("evidence", "transmitted")
    confidence = {
        "prepared": "prepared",
        "transmitted": "transmitted",
        "acknowledged": "acknowledged",
        "physical": "physically_confirmed",
    }.get(evidence, "transmitted")
    conn = db()
    conn.execute(
        "INSERT INTO checkpoints(job_id,y_mm,band_mm,state,evidence,confidence,created_at) VALUES(?,?,?,?,?,?,?)",
        (job_id, y_mm, band_mm, state, evidence, confidence, now()),
    )
    conn.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?", ("PRINTING", now(), job_id))
    record_event(conn, job_id, "CHECKPOINT", "operator_or_adapter", {"y_mm": y_mm, "evidence": evidence})
    conn.commit()
    conn.close()
    return jsonify(ok=True, job_id=job_id, y_mm=y_mm, confidence=confidence)


@app.post("/api/jobs/<job_id>/interrupt")
def interrupt(job_id):
    payload = request.get_json(silent=True) or request.form
    event_type = payload.get("event_type", "UNKNOWN_INTERRUPTION")
    source = payload.get("source", "operator")
    note = payload.get("note", "")
    conn = db()
    conn.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?", ("INTERRUPTED", now(), job_id))
    record_event(conn, job_id, event_type, source, {"note": note})
    conn.commit()
    conn.close()
    return jsonify(ok=True, status="INTERRUPTED")


@app.get("/api/jobs/<job_id>")
def job_detail(job_id):
    conn = db()
    job = row_dict(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
    if not job:
        conn.close()
        return jsonify(error="Job not found"), 404
    checkpoints = [row_dict(r) for r in conn.execute("SELECT * FROM checkpoints WHERE job_id=? ORDER BY y_mm", (job_id,)).fetchall()]
    events = [row_dict(r) for r in conn.execute("SELECT * FROM events WHERE job_id=? ORDER BY id", (job_id,)).fetchall()]
    conn.close()
    return jsonify(job=job, checkpoints=checkpoints, events=events)


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
        rec, confidence, mode, reason = "CONTINUE", "high", "certified_candidate", "Physical position was confirmed; adapter validation is still required."
        selected = cp["y_mm"]
    elif cp["confidence"] == "acknowledged":
        rec, confidence, mode, reason = "TEST_FIRST", "medium", "assisted", "Printer acknowledgement exists, but physical output may include buffering."
        selected = cp["y_mm"]
    else:
        rec, confidence, mode, reason = "TEST_FIRST", "low", "assisted", "Only host-side progress is known; use a registration strip or restart."
        selected = cp["y_mm"]
    conn.close()
    return jsonify(job_id=job_id, recommendation=rec, confidence=confidence, mode=mode, reason=reason, selected_y_mm=selected, overlap_mm=5)


@app.post("/api/jobs/<job_id>/continuation")
def continuation(job_id):
    payload = request.get_json(silent=True) or request.form
    y_mm = float(payload.get("y_mm", 0))
    overlap_mm = float(payload.get("overlap_mm", 5))
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return jsonify(error="Job not found"), 404
    source_path = Path(job["source_path"])
    output_name = f"{job_id}_continuation_from_{y_mm:.1f}mm.png"
    output_path = OUTPUT_DIR / output_name
    try:
        with Image.open(source_path) as im:
            if im.height <= 0:
                raise ValueError("Image has no height")
            ratio = y_mm / max(float(job["media_length_mm"] or im.height), 1.0)
            start_px = int(max(0, min(im.height - 1, ratio * im.height)))
            overlap_px = max(0, int(overlap_mm / max(float(job["media_length_mm"] or im.height), 1.0) * im.height))
            crop_start = max(0, start_px - overlap_px)
            im.crop((0, crop_start, im.width, im.height)).save(output_path)
    except Exception as exc:
        conn.close()
        return jsonify(error=f"Continuation generation failed: {exc}"), 400
    conn.execute(
        "INSERT INTO decisions(job_id,selected_y_mm,overlap_mm,mode,recommendation,confidence,operator_action,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (job_id, y_mm, overlap_mm, "assisted", "TEST_FIRST", "operator_selected", "generated_continuation", now()),
    )
    record_event(conn, job_id, "CONTINUATION_GENERATED", "recovery_engine", {"file": output_name, "y_mm": y_mm, "overlap_mm": overlap_mm})
    conn.commit()
    conn.close()
    return jsonify(ok=True, file=output_name, url=f"/outputs/{output_name}", selected_y_mm=y_mm, overlap_mm=overlap_mm)


@app.get("/outputs/<path:name>")
def outputs(name):
    return send_from_directory(OUTPUT_DIR, name, as_attachment=True)


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5173, debug=False)
