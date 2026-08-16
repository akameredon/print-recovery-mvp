import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    sample_path = Path(handle.name)
Image.new("RGB", (40, 40), "white").save(sample_path)

with sample_path.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("integrity.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id, source_path = conn.execute(
    "SELECT id,source_path FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("integrity.png",),
).fetchone()
conn.close()

verified = requests.get(BASE + f"/api/jobs/{job_id}/integrity")
assert verified.status_code == 200
assert verified.json()["status"] == "verified"

Path(source_path).write_bytes(b"tampered-content")
changed = requests.get(
    BASE + f"/api/jobs/{job_id}/integrity", headers={"X-Correlation-ID": "day14-changed"}
)
assert changed.status_code == 409
assert changed.json()["error"] == "SOURCE_CHANGED"
assert changed.json()["correlation_id"] == "day14-changed"

Path(source_path).unlink()
missing = requests.get(BASE + f"/api/jobs/{job_id}/integrity")
assert missing.status_code == 404
assert missing.json()["error"] == "SOURCE_MISSING"

conn = sqlite3.connect("data/print_recovery.sqlite3")
events = [
    row[0]
    for row in conn.execute("SELECT event_type FROM events WHERE job_id=? ORDER BY id", (job_id,))
]
conn.close()
assert events[-3:] == ["SOURCE_VERIFIED", "SOURCE_CHANGED", "SOURCE_MISSING"]
print({"status": "passed", "job_id": job_id, "states": ["verified", "changed", "missing"]})
