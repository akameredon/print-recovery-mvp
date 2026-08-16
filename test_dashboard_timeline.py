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
        files={"file": ("dashboard-timeline.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("dashboard-timeline.png",),
).fetchone()[0]
conn.close()

html = requests.get(BASE + "/?q=dashboard-timeline.png")
assert html.status_code == 200
assert "Show evidence timeline" in html.text
assert f"timeline-{job_id}" in html.text
assert "function timeline(id)" in html.text

api = requests.get(BASE + f"/api/jobs/{job_id}/timeline?limit=100")
assert api.status_code == 200
assert api.json()["items"][0]["event"] == "READY"
print({"status": "passed", "job_id": job_id, "timeline_control": True})
