import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (30, 30), "white").save(source)
with source.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("approval-dialog.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("approval-dialog.png",),
).fetchone()[0]
conn.close()
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 100, "band_mm": 5, "evidence": "physical"},
    ).status_code
    == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/continuation",
        json={"y_mm": 100, "overlap_mm": 5},
    ).status_code
    == 200
)
html = requests.get(BASE + "/?q=approval-dialog.png")
assert html.status_code == 200
for label in (
    "Review recovery decision",
    "Approve recovery decision",
    "Reject recovery decision",
    "Operator approval required",
):
    assert label in html.text
approved = requests.post(
    BASE + f"/api/jobs/{job_id}/review",
    json={"action": "approved", "note": "Registration strip checked"},
)
assert approved.status_code == 200, approved.text
summary = requests.get(BASE + f"/api/jobs/{job_id}/review")
assert summary.status_code == 200
assert summary.json()["review_state"] == "approved"
conn = sqlite3.connect("data/print_recovery.sqlite3")
event = conn.execute(
    "SELECT event_type,payload FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
).fetchone()
conn.close()
assert event[0] == "RECOVERY_REVIEWED"
assert "Registration strip checked" in event[1]
print({"status": "passed", "approval_dialog": True, "audit_event": event[0]})
