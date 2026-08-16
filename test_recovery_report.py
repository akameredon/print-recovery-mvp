import sqlite3
import tempfile

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (100, 200), "white").save(source)
with open(source, "rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("report.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("report.png",),
).fetchone()[0]
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint",
    json={"y_mm": 100, "evidence": "acknowledged"},
)
assert checkpoint.status_code == 200, checkpoint.text
interrupt = requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt",
    json={"reason": "POWER_LOSS", "note": "Utility outage during pass"},
)
assert interrupt.status_code == 200, interrupt.text
continuation = requests.post(
    BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 100, "overlap_mm": 5}
)
assert continuation.status_code == 200, continuation.text
review = requests.post(
    BASE + f"/api/jobs/{job_id}/review",
    json={"action": "approved", "note": "Report evidence reviewed"},
)
assert review.status_code == 200, review.text
report = requests.get(BASE + f"/api/jobs/{job_id}/recovery-report")
assert report.status_code == 200, report.text
body = report.json()
assert body["selected_coordinate"]["y_mm"] == 100
assert body["confidence"]["level"] == "medium"
assert body["source_integrity"]["status"] == "verified"
assert body["interruption"]["details"]["classification"]["classification"] == "outage"
assert body["operator_review"]["action"] == "approved"
assert body["recovery_safety"]["safe_to_generate"] is True
markdown = requests.get(BASE + f"/api/jobs/{job_id}/recovery-report?format=md")
assert markdown.status_code == 200
assert "# Recovery Report" in markdown.text
assert "Selected coordinate: **100.0 mm**" in markdown.text
invalid = requests.get(BASE + f"/api/jobs/{job_id}/recovery-report?format=xml")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_REPORT_FORMAT"
print({"status": "passed", "json": True, "markdown": True, "evidence": True})
