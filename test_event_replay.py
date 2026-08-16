import json
import sqlite3
import subprocess
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
        files={"file": ("replay.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("replay.png",),
).fetchone()[0]
conn.close()
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 100, "evidence": "acknowledged"},
    ).status_code
    == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/adapter/simulate",
        json={"event_type": "PROGRESS", "payload": {"y_mm": 100}},
    ).status_code
    == 200
)
before = Path("data/print_recovery.sqlite3").read_bytes()
result = subprocess.run(
    ["python3", "event_replay.py", "--job-id", job_id],
    check=True,
    capture_output=True,
    text=True,
)
replay = json.loads(result.stdout)
assert replay["job_id"] == job_id
assert replay["total"] >= 3
assert "checkpoint" in {item["kind"] for item in replay["items"]}
assert "event" in {item["kind"] for item in replay["items"]}
assert any(item.get("event") == "ADAPTER_PROGRESS" for item in replay["items"])
assert all(
    replay["items"][index]["timestamp"] <= replay["items"][index + 1]["timestamp"]
    for index in range(len(replay["items"]) - 1)
)
after = Path("data/print_recovery.sqlite3").read_bytes()
assert before == after
missing = subprocess.run(
    ["python3", "event_replay.py", "--job-id", "not-real"],
    capture_output=True,
    text=True,
)
assert missing.returncode != 0
assert "JOB_NOT_FOUND" in missing.stderr
print({"status": "passed", "replayed_items": replay["total"], "database_unchanged": True})
