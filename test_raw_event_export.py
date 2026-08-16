import json
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
        files={"file": ("raw-export.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("raw-export.png",),
).fetchone()[0]
raw_payload = conn.execute(
    "SELECT payload FROM events WHERE job_id=? AND event_type='JOB_CREATED' ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()[0]
conn.close()
export = requests.get(BASE + f"/api/jobs/{job_id}/events/raw")
assert export.status_code == 200, export.text
assert export.headers["Content-Type"].startswith("application/x-ndjson")
assert f"{job_id}_raw_events.jsonl" in export.headers["Content-Disposition"]
rows = [json.loads(line) for line in export.text.splitlines()]
created = [row for row in rows if row["event_type"] == "JOB_CREATED"][-1]
assert created["payload_raw"] == raw_payload
invalid = requests.get(BASE + f"/api/jobs/{job_id}/events/raw?format=json")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_RAW_EVENT_FORMAT"
missing = requests.get(BASE + "/api/jobs/not-real/events/raw")
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
html = requests.get(BASE + "/?q=raw-export.png")
assert "Download raw events" in html.text
print({"status": "passed", "raw_events": len(rows), "payload_exact": True})
