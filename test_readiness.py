import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"


def create_job(name):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        source = Path(handle.name)
    Image.new("RGB", (50, 50), "white").save(source)
    with source.open("rb") as image_file:
        response = requests.post(
            BASE + "/api/jobs",
            files={"file": (name, image_file, "image/png")},
            data={"media_width_mm": "100", "media_length_mm": "200"},
            allow_redirects=False,
        )
    assert response.status_code == 302, response.text
    conn = sqlite3.connect("data/print_recovery.sqlite3")
    job_id, stored_path = conn.execute(
        "SELECT id,source_path FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
        (name,),
    ).fetchone()
    conn.close()
    return job_id, Path(stored_path)


blocked_id, blocked_path = create_job("blocked.png")
blocked = requests.get(BASE + f"/api/jobs/{blocked_id}/readiness")
assert blocked.status_code == 200
assert blocked.json()["readiness"] == "blocked"
assert blocked.json()["checkpoint"] is None

review_id, _ = create_job("review.png")
checkpoint = requests.post(
    BASE + f"/api/jobs/{review_id}/checkpoint",
    json={"y_mm": 120, "band_mm": 5, "evidence": "acknowledged"},
)
assert checkpoint.status_code == 200, checkpoint.text
review = requests.get(
    BASE + f"/api/jobs/{review_id}/readiness",
    headers={"X-Correlation-ID": "day15-review"},
)
assert review.status_code == 200
assert review.json()["readiness"] == "review_required"
assert review.json()["checkpoint"]["y_mm"] == 120.0
assert review.json()["operator_confirmation_required"] is True
assert review.json()["request_correlation_id"] == "day15-review"

ready_id, _ = create_job("ready.png")
assert (
    requests.post(
        BASE + f"/api/jobs/{ready_id}/checkpoint",
        json={"y_mm": 240, "band_mm": 5, "evidence": "physical"},
    ).status_code
    == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{ready_id}/interrupt",
        json={"event_type": "POWER_LOSS", "source": "operator", "note": "Day 15 test"},
    ).status_code
    == 200
)
ready = requests.get(BASE + f"/api/jobs/{ready_id}/readiness")
assert ready.status_code == 200
assert ready.json()["readiness"] == "ready_for_operator_review"
assert ready.json()["interruption"]["to_status"] == "INTERRUPTED"

blocked_path.write_bytes(b"changed")
changed = requests.get(BASE + f"/api/jobs/{blocked_id}/readiness")
assert changed.json()["readiness"] == "blocked"
assert changed.json()["source_integrity"]["status"] == "changed"

missing = requests.get(BASE + "/api/jobs/not-a-real-job/readiness")
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
print({"status": "passed", "states": ["blocked", "review_required", "ready_for_operator_review"]})
