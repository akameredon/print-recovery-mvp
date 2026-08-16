import json
import sqlite3
import tempfile

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (100, 200), "white").save(source)
with open(source, "rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("review-strip.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("review-strip.png",),
).fetchone()[0]
conn.close()
pending = requests.get(BASE + f"/api/jobs/{job_id}/registration-strip/review")
assert pending.status_code == 200
assert pending.json()["review_state"] == "pending"
assert pending.json()["operator_confirmation_required"] is True
no_strip = requests.post(
    BASE + f"/api/jobs/{job_id}/registration-strip/review", json={"result": "aligned"}
)
assert no_strip.status_code == 409
assert no_strip.json()["error"] == "NO_REGISTRATION_STRIP"
strip = requests.post(
    BASE + f"/api/jobs/{job_id}/registration-strip", json={"y_mm": 100, "strip_height_mm": 20}
)
assert strip.status_code == 200, strip.text
review = requests.post(
    BASE + f"/api/jobs/{job_id}/registration-strip/review",
    json={"result": "aligned", "note": "Registration line matched the test mark."},
)
assert review.status_code == 200, review.text
body = review.json()
assert body["result"] == "aligned"
assert body["file"] == strip.json()["file"]
summary = requests.get(BASE + f"/api/jobs/{job_id}/registration-strip/review")
assert summary.json()["review_state"] == "aligned"
assert summary.json()["operator_confirmation_required"] is False
assert summary.json()["latest_review"]["details"]["note"].startswith("Registration line")
invalid = requests.post(
    BASE + f"/api/jobs/{job_id}/registration-strip/review", json={"result": "bad"}
)
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_REGISTRATION_RESULT"
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT event_type,payload FROM events WHERE job_id=? AND event_type='REGISTRATION_STRIP_REVIEWED' ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()
conn.close()
assert row[0] == "REGISTRATION_STRIP_REVIEWED"
assert json.loads(row[1])["result"] == "aligned"
print({"status": "passed", "pending": True, "confirmed": True, "audited": True})
