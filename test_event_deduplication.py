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
        files={"file": ("deduplication.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("deduplication.png",),
).fetchone()[0]
conn.close()
payload = {"reason": "POWER_LOSS", "source": "operator", "note": "Utility outage"}
first = requests.post(BASE + f"/api/jobs/{job_id}/interrupt", json=payload)
second = requests.post(BASE + f"/api/jobs/{job_id}/interrupt", json=payload)
assert first.status_code == 200
assert second.status_code == 200
changed = requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt",
    json={**payload, "note": "Utility outage confirmed by operator"},
)
assert changed.status_code == 200
conn = sqlite3.connect("data/print_recovery.sqlite3")
rows = conn.execute(
    "SELECT event_type,payload FROM events WHERE job_id=? AND event_type='POWER_LOSS' ORDER BY id",
    (job_id,),
).fetchall()
conn.close()
assert len(rows) == 2
assert '"note": "Utility outage"' in rows[0][1]
assert "confirmed by operator" in rows[1][1]
print({"status": "passed", "events_after_repeats": len(rows), "distinct_change_preserved": True})
