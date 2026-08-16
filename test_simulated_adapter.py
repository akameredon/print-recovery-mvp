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
        files={"file": ("adapter.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("adapter.png",),
).fetchone()[0]
conn.close()
event = requests.post(
    BASE + f"/api/jobs/{job_id}/adapter/simulate",
    json={"event_type": "PROGRESS", "payload": {"y_mm": 240, "pass_number": 2}},
)
assert event.status_code == 200, event.text
body = event.json()
assert body["adapter"] == "simulated_adapter"
assert body["event_type"] == "PROGRESS"
assert body["source"] == "simulated_adapter"
assert body["payload"]["y_mm"] == 240
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT event_type,source,payload FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()
conn.close()
assert row[0] == "ADAPTER_PROGRESS"
assert row[1] == "simulated_adapter"
assert '"y_mm": 240' in row[2]
invalid = requests.post(
    BASE + f"/api/jobs/{job_id}/adapter/simulate", json={"event_type": "NOT_SUPPORTED"}
)
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_ADAPTER_EVENT"
missing = requests.post(
    BASE + "/api/jobs/not-real/adapter/simulate", json={"event_type": "PROGRESS"}
)
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
print({"status": "passed", "adapter": "simulated_adapter", "event": "PROGRESS"})
