import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (60, 60), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("review.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "250"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text

conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id, stored_path = conn.execute(
    "SELECT id,source_path FROM jobs ORDER BY created_at DESC LIMIT 1"
).fetchone()
conn.close()
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 90, "band_mm": 5, "evidence": "physical"},
    ).status_code
    == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/continuation",
        json={"y_mm": 90, "overlap_mm": 5},
    ).status_code
    == 200
)

approved = requests.post(
    BASE + f"/api/jobs/{job_id}/review",
    json={"action": "approved", "note": "Registration strip checked"},
    headers={"X-Correlation-ID": "day17-approved"},
)
assert approved.status_code == 200, approved.text
assert approved.json()["action"] == "approved"
assert approved.json()["operator_confirmation_required"] is True
assert approved.json()["request_correlation_id"] == "day17-approved"

rejected = requests.post(
    BASE + f"/api/jobs/{job_id}/review",
    data={"action": "rejected", "note": "Visual alignment failed"},
)
assert rejected.status_code == 200, rejected.text
assert rejected.json()["action"] == "rejected"

conn = sqlite3.connect("data/print_recovery.sqlite3")
operator_action = conn.execute(
    "SELECT operator_action FROM decisions WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
).fetchone()[0]
events = [
    row[0]
    for row in conn.execute("SELECT event_type FROM events WHERE job_id=? ORDER BY id", (job_id,))
]
conn.close()
assert operator_action == "rejected: Visual alignment failed"
assert events[-2:] == ["RECOVERY_REVIEWED", "RECOVERY_REVIEWED"]

invalid = requests.post(BASE + f"/api/jobs/{job_id}/review", json={"action": "maybe"})
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_REVIEW_ACTION"
long_note = requests.post(
    BASE + f"/api/jobs/{job_id}/review", json={"action": "approved", "note": "x" * 1001}
)
assert long_note.status_code == 400
assert long_note.json()["error"] == "INVALID_REVIEW_NOTE"

no_decision_id = requests.post(
    BASE + "/api/jobs/not-a-real-job/review", json={"action": "approved"}
)
assert no_decision_id.status_code == 404
assert no_decision_id.json()["error"] == "JOB_NOT_FOUND"
print({"status": "passed", "actions": ["approved", "rejected"]})
