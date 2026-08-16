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
        files={"file": ("band-pass.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("band-pass.png",),
).fetchone()[0]
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint",
    json={"y_mm": 100, "evidence": "transmitted", "logical_band": 7, "pass_number": 2},
)
assert checkpoint.status_code == 200, checkpoint.text
assert checkpoint.json()["logical_band"] == 7
assert checkpoint.json()["pass_number"] == 2
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT logical_band,pass_number FROM checkpoints WHERE job_id=? ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()
payload = conn.execute(
    "SELECT payload FROM events WHERE job_id=? AND event_type='CHECKPOINT' ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()[0]
conn.close()
assert row == (7, 2)
assert json.loads(payload)["logical_band"] == 7
assert json.loads(payload)["pass_number"] == 2
invalid = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint", json={"y_mm": 100, "logical_band": -1}
)
assert invalid.status_code == 500 or invalid.status_code == 400
html = requests.get(BASE + "/?q=band-pass.png")
assert html.status_code == 200
assert "Logical band" in html.text
assert "Pass number" in html.text
print({"status": "passed", "logical_band": 7, "pass_number": 2})
