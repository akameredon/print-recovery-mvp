import json
import sqlite3
import tempfile

import requests
from PIL import Image

from signal_matrix import assess_signal_matrix

host_only = assess_signal_matrix(["host_job_created", "host_transmission_completed"])
assert host_only["status"] == "assessed"
assert host_only["available_families"] == ["host"]
assert host_only["recovery_mode"] == "assisted_restart_or_registration_check"
assert "host-side signals" in host_only["confidence_limit"]
progress = assess_signal_matrix(["rip_queue_seen", "rip_progress_percent"])
assert progress["available_families"] == ["rip"]
assert progress["recovery_mode"] == "assisted_test_first"
physical = assess_signal_matrix(["physical_checkpoint"])
assert physical["available_families"] == ["physical"]
assert physical["recovery_mode"] == "assisted_review_required"
assert any(
    row["signal"] == "printer_status_feedback" and not row["available"] for row in physical["rows"]
)

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (80, 160), "white").save(source)
with open(source, "rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("signals.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("signals.png",),
).fetchone()[0]
conn.close()
assessed = requests.post(
    BASE + f"/api/jobs/{job_id}/signals/assess",
    json={
        "source": "synthetic_signal_observer",
        "signals": ["host_transmission_started", "rip_progress_percent"],
    },
)
assert assessed.status_code == 200, assessed.text
body = assessed.json()["assessment"]
assert body["recovery_mode"] == "assisted_test_first"
assert "rip" in body["available_families"]
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT event_type,payload,source FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()
conn.close()
assert row[0] == "SIGNAL_MATRIX_ASSESSED"
assert row[2] == "synthetic_signal_observer"
assert json.loads(row[1])["signals"] == ["host_transmission_started", "rip_progress_percent"]
invalid = requests.post(BASE + f"/api/jobs/{job_id}/signals/assess", json={"signals": "not-a-list"})
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_SIGNAL_LIST"
print({"status": "passed", "families": ["host", "rip", "printer", "physical"], "persisted": True})
