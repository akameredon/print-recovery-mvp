import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    sample_path = Path(handle.name)
Image.new("RGB", (40, 40), "white").save(sample_path)

with sample_path.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("history.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("history.png",),
).fetchone()[0]
conn.close()

assert (
    requests.post(BASE + f"/api/jobs/{job_id}/checkpoint", data={"y_mm": "50"}).status_code == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/interrupt", json={"event_type": "POWER_OR_PROTECTION_TRIP"}
    ).status_code
    == 200
)

page_one = requests.get(BASE + f"/api/jobs/{job_id}/status-history?page=1&per_page=2")
assert page_one.status_code == 200
body_one = page_one.json()
assert body_one["total"] == 3
assert body_one["pages"] == 2
assert body_one["has_next"] is True
assert [item["to_status"] for item in body_one["items"]] == ["READY", "PRINTING"]

page_two = requests.get(BASE + f"/api/jobs/{job_id}/status-history?page=2&per_page=2")
assert page_two.status_code == 200
body_two = page_two.json()
assert body_two["has_previous"] is True
assert [item["to_status"] for item in body_two["items"]] == ["INTERRUPTED"]

invalid = requests.get(BASE + f"/api/jobs/{job_id}/status-history?page=0&per_page=101")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_PAGINATION"

missing = requests.get(BASE + "/api/jobs/not-a-real-job/status-history")
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
print(
    {"status": "passed", "job_id": job_id, "pages": body_one["pages"], "total": body_one["total"]}
)
