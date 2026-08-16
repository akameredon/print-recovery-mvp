import os
import signal
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
PID_FILE = Path("/tmp/print-recovery-mvp.pid")
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (30, 30), "white").save(source)
with source.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("durability.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("durability.png",),
).fetchone()[0]
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint",
    json={"y_mm": 275, "evidence": "acknowledged", "logical_band": 3, "pass_number": 1},
)
assert checkpoint.status_code == 200, checkpoint.text
assert PID_FILE.exists()
old_pid = int(PID_FILE.read_text())
os.kill(old_pid, signal.SIGTERM)
for _ in range(20):
    if not Path(f"/proc/{old_pid}").exists():
        break
    time.sleep(0.1)
new_process = subprocess.Popen(
    ["python3", "app.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
try:
    for _ in range(30):
        try:
            health = requests.get(BASE + "/healthz", timeout=0.3)
            if health.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.2)
    detail = requests.get(BASE + f"/api/jobs/{job_id}")
    assert detail.status_code == 200, detail.text
    checkpoints = detail.json()["checkpoints"]
    match = [item for item in checkpoints if item["y_mm"] == 275.0][-1]
    assert match["logical_band"] == 3
    assert match["pass_number"] == 1
    conn = sqlite3.connect("data/print_recovery.sqlite3")
    event_count = conn.execute(
        "SELECT COUNT(*) FROM events WHERE job_id=? AND event_type='CHECKPOINT'", (job_id,)
    ).fetchone()[0]
    conn.close()
    assert event_count >= 1
finally:
    new_process.terminate()
    new_process.wait(timeout=5)
print({"status": "passed", "checkpoint_survived_restart": True, "event_count": event_count})
