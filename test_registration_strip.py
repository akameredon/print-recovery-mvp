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
        files={"file": ("registration.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200", "overlap_mm": "5"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id, source_hash = conn.execute(
    "SELECT id,source_hash FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("registration.png",),
).fetchone()
conn.close()
first = requests.post(
    BASE + f"/api/jobs/{job_id}/registration-strip",
    json={"y_mm": 100, "strip_height_mm": 20},
)
second = requests.post(
    BASE + f"/api/jobs/{job_id}/registration-strip",
    json={"y_mm": 100, "strip_height_mm": 20},
)
assert first.status_code == 200, first.text
assert second.status_code == 200, second.text
first_body = first.json()
second_body = second.json()
assert first_body["version"] == 1
assert second_body["version"] == 2
assert first_body["file"] != second_body["file"]
assert source_hash[:12] in first_body["file"]
assert first_body["operator_confirmation_required"] is True
assert first_body["crop_top_y_mm"] == 90.0
assert first_body["crop_bottom_y_mm"] == 110.0
image = requests.get(BASE + first_body["url"])
assert image.status_code == 200
assert image.headers["Content-Type"].startswith("image/")
with Image.open(source) as source_image:
    assert source_image.size == (100, 200)
conn = sqlite3.connect("data/print_recovery.sqlite3")
rows = conn.execute(
    "SELECT event_type,payload FROM events WHERE job_id=? AND event_type='REGISTRATION_STRIP_GENERATED' ORDER BY id",
    (job_id,),
).fetchall()
conn.close()
assert [json.loads(row[1])["version"] for row in rows[-2:]] == [1, 2]
assert all(json.loads(row[1])["source_hash"] == source_hash for row in rows[-2:])
invalid = requests.post(BASE + f"/api/jobs/{job_id}/registration-strip", json={"y_mm": -1})
assert invalid.status_code == 400
assert invalid.json()["error"] == "REGISTRATION_STRIP_FAILED"
print({"status": "passed", "versions": [1, 2], "rendered": True, "traceable": True})
