import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (60, 60), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("review-summary.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "250"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text

conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("review-summary.png",),
).fetchone()[0]
conn.close()
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 90, "band_mm": 5, "evidence": "physical"},
    ).status_code
    == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/continuation",
        json={"y_mm": 90, "overlap_mm": 5},
    ).status_code
    == 200
)

pending = requests.get(
    BASE + f"/api/jobs/{job_id}/review",
    headers={"X-Correlation-ID": "day18-pending"},
)
assert pending.status_code == 200, pending.text
assert pending.json()["review_state"] == "pending"
assert pending.json()["review_events"] == []
assert pending.json()["operator_confirmation_required"] is True
assert pending.json()["request_correlation_id"] == "day18-pending"

approved = requests.post(
    BASE + f"/api/jobs/{job_id}/review",
    json={"action": "approved", "note": "Alignment confirmed"},
)
assert approved.status_code == 200, approved.text
approved_summary = requests.get(BASE + f"/api/jobs/{job_id}/review")
assert approved_summary.status_code == 200
assert approved_summary.json()["review_state"] == "approved"
assert approved_summary.json()["operator_confirmation_required"] is False
assert len(approved_summary.json()["review_events"]) == 1
assert approved_summary.json()["review_events"][0]["details"]["note"] == "Alignment confirmed"

rejected = requests.post(
    BASE + f"/api/jobs/{job_id}/review",
    data={"action": "rejected", "note": "Second check failed"},
)
assert rejected.status_code == 200, rejected.text
rejected_summary = requests.get(BASE + f"/api/jobs/{job_id}/review")
assert rejected_summary.json()["review_state"] == "rejected"
assert len(rejected_summary.json()["review_events"]) == 2
assert rejected_summary.json()["review_events"][-1]["details"]["action"] == "rejected"

with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    no_decision_source = Path(handle.name)
Image.new("RGB", (20, 20), "black").save(no_decision_source)
with no_decision_source.open("rb") as image_file:
    no_decision_created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("no-decision.png", image_file, "image/png")},
        allow_redirects=False,
    )
assert no_decision_created.status_code == 302
conn = sqlite3.connect("data/print_recovery.sqlite3")
no_decision_id = conn.execute("SELECT id FROM jobs ORDER BY created_at DESC LIMIT 1").fetchone()[0]
conn.close()
no_decision = requests.get(BASE + f"/api/jobs/{no_decision_id}/review")
assert no_decision.status_code == 409
assert no_decision.json()["error"] == "NO_DECISION"
missing = requests.get(BASE + "/api/jobs/not-a-real-job/review")
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
print({"status": "passed", "states": ["pending", "approved", "rejected"]})
