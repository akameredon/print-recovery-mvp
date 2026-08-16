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
        files={"file": ("interruption-reasons.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("interruption-reasons.png",),
).fetchone()[0]
conn.close()

recorded = requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt",
    json={
        "reason": "PROTECTION_TRIP",
        "source": "operator",
        "note": "Lightning protection opened the machine safety switch.",
    },
)
assert recorded.status_code == 200, recorded.text
assert recorded.json()["reason"] == "PROTECTION_TRIP"
assert recorded.json()["note"].startswith("Lightning protection")
conn = sqlite3.connect("data/print_recovery.sqlite3")
event_type, payload = conn.execute(
    "SELECT event_type,payload FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
).fetchone()
conn.close()
assert event_type == "PROTECTION_TRIP"
stored_payload = json.loads(payload)
assert stored_payload["reason"] == "PROTECTION_TRIP"
assert stored_payload["note"] == "Lightning protection opened the machine safety switch."
assert stored_payload["classification"]["classification"] == "outage"
assert stored_payload["classification"]["source"] == "operator"

invalid = requests.post(BASE + f"/api/jobs/{job_id}/interrupt", json={"reason": "NOT_A_REASON"})
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_INTERRUPTION_REASON"
long_note = requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt",
    json={"reason": "POWER_LOSS", "note": "x" * 1001},
)
assert long_note.status_code == 400
assert long_note.json()["error"] == "INVALID_INTERRUPTION_NOTE"
missing = requests.post(BASE + "/api/jobs/not-a-real-job/interrupt", json={"reason": "POWER_LOSS"})
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
html = requests.get(BASE + "/?q=interruption-reasons.png")
assert html.status_code == 200
for label in ("Power loss", "Lightning/protection trip", "Communication loss", "Interruption note"):
    assert label in html.text
print({"status": "passed", "reason": "PROTECTION_TRIP", "note_saved": True})
