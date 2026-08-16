import json
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (100, 200), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("overlap.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200", "overlap_mm": "12.5"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("overlap.png",),
).fetchone()[0]
stored = conn.execute("SELECT overlap_mm FROM jobs WHERE id=?", (job_id,)).fetchone()[0]
conn.close()
assert stored == 12.5
preview = requests.get(BASE + f"/api/jobs/{job_id}/continuation-preview", params={"y_mm": 100})
assert preview.status_code == 200, preview.text
assert preview.json()["overlap_mm"] == 12.5
assert preview.json()["regions"][0]["end_y_mm"] == 87.5
updated = requests.post(BASE + f"/api/jobs/{job_id}/overlap", json={"overlap_mm": 20})
assert updated.status_code == 200, updated.text
assert updated.json()["overlap_mm"] == 20
preview_after = requests.get(
    BASE + f"/api/jobs/{job_id}/continuation-preview", params={"y_mm": 100}
)
assert preview_after.json()["overlap_mm"] == 20
assert preview_after.json()["regions"][0]["end_y_mm"] == 80.0
continuation = requests.post(BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 100})
assert continuation.status_code == 200, continuation.text
assert continuation.json()["overlap_mm"] == 20
conn = sqlite3.connect("data/print_recovery.sqlite3")
event = conn.execute(
    "SELECT event_type,payload FROM events WHERE job_id=? ORDER BY id DESC LIMIT 2", (job_id,)
).fetchall()
conn.close()
assert event[0][0] == "CONTINUATION_GENERATED"
assert json.loads(event[0][1])["overlap_mm"] == 20
assert any(row[0] == "JOB_OVERLAP_UPDATED" for row in event)
invalid = requests.post(BASE + f"/api/jobs/{job_id}/overlap", json={"overlap_mm": -1})
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_OVERLAP"
print({"status": "passed", "created_overlap_mm": 12.5, "updated_overlap_mm": 20.0})
