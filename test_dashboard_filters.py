import os
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
TOKEN = f"day21-{os.getpid()}"


def create_job(name):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        source = Path(handle.name)
    Image.new("RGB", (30, 30), "white").save(source)
    with source.open("rb") as image_file:
        response = requests.post(
            BASE + "/api/jobs",
            files={"file": (name, image_file, "image/png")},
            data={"media_width_mm": "100", "media_length_mm": "200"},
            allow_redirects=False,
        )
    assert response.status_code == 302, response.text
    conn = sqlite3.connect("data/print_recovery.sqlite3")
    job_id = conn.execute(
        "SELECT id FROM jobs WHERE file_name=? ORDER BY id DESC LIMIT 1", (name,)
    ).fetchone()[0]
    conn.close()
    return job_id


active_name = f"{TOKEN}-active-filter.png"
interrupted_name = f"{TOKEN}-interrupted-filter.png"
completed_name = f"{TOKEN}-completed-filter.png"
active_id = create_job(active_name)
interrupted_id = create_job(interrupted_name)
assert (
    requests.post(
        BASE + f"/api/jobs/{interrupted_id}/interrupt",
        json={"event_type": "POWER_LOSS", "source": "operator"},
    ).status_code
    == 200
)
completed_id = create_job(completed_name)
conn = sqlite3.connect("data/print_recovery.sqlite3")
conn.execute("UPDATE jobs SET status='COMPLETED' WHERE id=?", (completed_id,))
conn.commit()
conn.close()

all_jobs = requests.get(BASE + "/api/jobs?filter=all")
active_jobs = requests.get(BASE + "/api/jobs?filter=active")
interrupted_jobs = requests.get(BASE + "/api/jobs?filter=interrupted")
completed_jobs = requests.get(BASE + "/api/jobs?filter=completed")
for response in (all_jobs, active_jobs, interrupted_jobs, completed_jobs):
    assert response.status_code == 200, response.text
assert all_jobs.json()["filter"] == "all"
assert active_id in {job["id"] for job in active_jobs.json()["jobs"]}
assert interrupted_id in {job["id"] for job in interrupted_jobs.json()["jobs"]}
assert completed_id in {job["id"] for job in completed_jobs.json()["jobs"]}
assert interrupted_id not in {job["id"] for job in active_jobs.json()["jobs"]}
assert completed_id not in {job["id"] for job in active_jobs.json()["jobs"]}
assert all_jobs.json()["count"] >= (
    active_jobs.json()["count"] + interrupted_jobs.json()["count"] + completed_jobs.json()["count"]
)

html = requests.get(BASE + "/?filter=interrupted")
assert html.status_code == 200
assert "interrupted-filter.png" in html.text
assert "completed-filter.png" not in html.text
assert 'value="interrupted" selected' in html.text

invalid = requests.get(BASE + "/api/jobs?filter=unknown")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_JOB_QUERY"
print({"status": "passed", "filters": ["all", "active", "interrupted", "completed"]})
