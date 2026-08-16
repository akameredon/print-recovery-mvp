import tempfile
from pathlib import Path

import requests
from PIL import Image

from app import db

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (60, 60), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("timeline.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "250"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text

conn = db()
job_id = conn.execute("SELECT id FROM jobs ORDER BY created_at DESC LIMIT 1").fetchone()[0]
conn.close()
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 80, "band_mm": 5, "evidence": "acknowledged"},
    ).status_code
    == 200
)
assert (
    requests.post(
        BASE + f"/api/jobs/{job_id}/interrupt",
        json={"event_type": "POWER_LOSS", "source": "operator", "note": "timeline test"},
    ).status_code
    == 200
)
recommendation = requests.get(BASE + f"/api/jobs/{job_id}/recommendation")
assert recommendation.status_code == 200, recommendation.text
continuation = requests.post(
    BASE + f"/api/jobs/{job_id}/continuation",
    json={"y_mm": 80, "overlap_mm": 5},
)
assert continuation.status_code == 200, continuation.text

timeline = requests.get(
    BASE + f"/api/jobs/{job_id}/timeline?limit=50",
    headers={"X-Correlation-ID": "day16-timeline"},
)
assert timeline.status_code == 200, timeline.text
payload = timeline.json()
assert payload["request_correlation_id"] == "day16-timeline"
assert payload["truncated"] is False
assert {item["kind"] for item in payload["items"]} >= {
    "event",
    "checkpoint",
    "status_transition",
    "decision",
}
timestamps = [item["timestamp"] for item in payload["items"]]
assert timestamps == sorted(timestamps)
assert any(item["event"] == "POWER_LOSS" for item in payload["items"])

limited = requests.get(BASE + f"/api/jobs/{job_id}/timeline?limit=2")
assert limited.status_code == 200
assert limited.json()["truncated"] is True
assert len(limited.json()["items"]) == 2

invalid = requests.get(BASE + f"/api/jobs/{job_id}/timeline?limit=0")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_LIMIT"
missing = requests.get(BASE + "/api/jobs/not-a-real-job/timeline")
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
print(
    {
        "status": "passed",
        "kinds": sorted({item["kind"] for item in payload["items"]}),
        "total": payload["total"],
    }
)
