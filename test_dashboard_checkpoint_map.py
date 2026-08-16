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
        files={"file": ("checkpoint-map.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "300"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("checkpoint-map.png",),
).fetchone()[0]
conn.close()
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 75, "band_mm": 5, "evidence": "physical"},
    ).status_code
    == 200
)
html = requests.get(BASE + "/?q=checkpoint-map.png")
assert html.status_code == 200
assert "Show checkpoint map" in html.text
assert f"map-{job_id}" in html.text
assert "function checkpointMap(id)" in html.text
assert "Checkpoint positions by Y coordinate" in html.text
job = requests.get(BASE + f"/api/jobs/{job_id}")
assert job.status_code == 200
assert job.json()["checkpoints"][0]["y_mm"] == 75.0
print({"status": "passed", "job_id": job_id, "checkpoint_map": True})
