import json
import os
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

from config import load_config

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (30, 30), "white").save(source)
with source.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("interval.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("interval.png",),
).fetchone()[0]
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint", json={"y_mm": 100, "evidence": "transmitted"}
)
assert checkpoint.status_code == 200, checkpoint.text
assert checkpoint.json()["checkpoint_interval_mm"] == 100.0
conn = sqlite3.connect("data/print_recovery.sqlite3")
payload = conn.execute(
    "SELECT payload FROM events WHERE job_id=? AND event_type='CHECKPOINT' ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()[0]
conn.close()
assert json.loads(payload)["interval_mm"] == 100.0
html = requests.get(BASE + "/?q=interval.png")
assert html.status_code == 200
assert "Configured checkpoint interval: 100.0 mm" in html.text
assert 'step="100.0"' in html.text

with tempfile.TemporaryDirectory() as directory:
    config_path = Path(directory) / "config.json"
    config_path.write_text('{"checkpoint_interval_mm": 0}', encoding="utf-8")
    previous = os.environ.get("PRINT_RECOVERY_CONFIG")
    os.environ["PRINT_RECOVERY_CONFIG"] = str(config_path)
    try:
        try:
            load_config(Path(directory))
        except ValueError as error:
            assert "checkpoint_interval_mm must be positive" in str(error)
        else:
            raise AssertionError("zero checkpoint interval was accepted")
    finally:
        if previous is None:
            os.environ.pop("PRINT_RECOVERY_CONFIG", None)
        else:
            os.environ["PRINT_RECOVERY_CONFIG"] = previous
print({"status": "passed", "interval_mm": 100.0, "event_recorded": True})
