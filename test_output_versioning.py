import json
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

from output_naming import continuation_output_name

assert continuation_output_name("job123", "abc123XYZ", 1, 90, 5) == (
    "continuation-v001_job123_abc123XYZ_from-90.0mm_overlap-5.0mm.png"
)
try:
    continuation_output_name("job123", "hash", 0, 90, 5)
except ValueError:
    pass
else:
    raise AssertionError("zero version was accepted")

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (100, 200), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("versioning.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200", "overlap_mm": "5"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id, source_hash = conn.execute(
    "SELECT id,source_hash FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("versioning.png",),
).fetchone()
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint", json={"y_mm": 90, "evidence": "transmitted"}
)
assert checkpoint.status_code == 200, checkpoint.text
first = requests.post(BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 90, "overlap_mm": 5})
second = requests.post(
    BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 90, "overlap_mm": 5}
)
assert first.status_code == 200, first.text
assert second.status_code == 200, second.text
first_body = first.json()
second_body = second.json()
assert first_body["version"] == 1
assert second_body["version"] == 2
assert first_body["file"] != second_body["file"]
assert source_hash[:12] in first_body["file"]
assert source_hash[:12] in second_body["file"]
assert Path(first_body["file"].replace("", "")).name == first_body["file"]
conn = sqlite3.connect("data/print_recovery.sqlite3")
rows = conn.execute(
    "SELECT payload FROM events WHERE job_id=? AND event_type='CONTINUATION_GENERATED' ORDER BY id",
    (job_id,),
).fetchall()
conn.close()
assert [json.loads(row[0])["version"] for row in rows[-2:]] == [1, 2]
assert all(json.loads(row[0])["source_hash"] == source_hash for row in rows[-2:])
print({"status": "passed", "versions": [1, 2], "traceable": True})
